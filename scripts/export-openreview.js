/* Run in the console of https://openreview.net while logged in.
 * Reads public API data and downloads JSON. Does not read or export credentials.
 * Re-running on the same page reuses successful requests from the in-memory cache.
 */
(function (root) {
  "use strict";

  const API = "https://api2.openreview.net";
  const WEBSITE = "https://openreview.net";
  const VENUES = ["ICLR.cc/2024/Conference", "NeurIPS.cc/2024/Conference"];
  const unwrap = (content, field) => {
    const item = content?.[field];
    return item && typeof item === "object" && "value" in item ? item.value : item;
  };
  const publicNote = (note) => Array.isArray(note.readers) && note.readers.includes("everyone");

  function validateSelection(selection, target) {
    if (selection === null) return;
    if (!selection || selection.schema_version !== 1 || !selection.venues ||
        typeof selection.venues !== "object" || Array.isArray(selection.venues) ||
        Object.keys(selection.venues).sort().join("|") !== VENUES.slice().sort().join("|")) {
      throw new Error("Topic selection must name exactly the two configured conferences.");
    }
    const seen = new Set();
    for (const venue of VENUES) {
      const ids = selection.venues[venue];
      if (!Array.isArray(ids) || ids.length !== target) {
        throw new Error(`Topic selection must contain exactly ${target} IDs for ${venue}.`);
      }
      for (const id of ids) {
        if (typeof id !== "string" || !/^[A-Za-z0-9_-]+$/.test(id) || seen.has(id)) {
          throw new Error("Topic selection contains a duplicate or invalid note ID.");
        }
        seen.add(id);
      }
    }
  }

  function topicMatch(note) {
    const title = unwrap(note.content, "title");
    const abstract = unwrap(note.content, "abstract");
    if (typeof title !== "string" || typeof abstract !== "string") return false;
    const text = `${title}\n${abstract}`.toLowerCase();
    const language = /\b(?:llms?|(?:large\s+)?language\s+models?|text\s+generation)\b/.test(text);
    const direct = /quantiz|quantis|\bkv[\s-]*cache\b|speculative\s+decod|\blow[\s-]*bit\b/.test(text);
    const method = /prun|sparsi|distill|compress|efficien|accelerat|early[\s-]*exit|latency|throughput|speedup|\bfaster\b/.test(text);
    const inference = /\b(?:inference|decoding|latency|throughput|deployment|serving)\b/.test(text);
    return language && (direct || (method && inference));
  }

  function ratingFields(fields) {
    const result = [];
    for (const [name, field] of Object.entries(fields)) {
      const param = field?.value?.param || field?.param || {};
      const options = param.enum;
      const numeric = ["integer", "number", "float"].includes(param.type);
      const scoredEnum = Array.isArray(options) && options.length > 1 && options.every((item) =>
        typeof item === "number" || (typeof item === "string" &&
          /^\s*\d+(?:\.\d+)?(?:\s*[:.)-]|\s+|$)/.test(item)));
      if (numeric || scoredEnum) result.push(name);
    }
    return result.sort();
  }

  function createExporter(options = {}) {
    const transport = options.fetch || root.fetch.bind(root);
    const crypto = options.crypto || root.crypto;
    const sleep = options.sleep || ((ms) => new Promise((resolve) => setTimeout(resolve, ms)));
    const progress = options.progress || ((message) => console.log(message));
    const cache = options.cache || new Map();
    const selection = options.selection ?? null;
    const target = options.targetPerVenue ?? 30;
    const pageSize = options.pageSize ?? 500;
    if (!Number.isInteger(target) || target < 1 || target > 50) throw new Error("Bad target.");
    if (!Number.isInteger(pageSize) || pageSize < 1 || pageSize > 1000) {
      throw new Error("Bad page size.");
    }
    validateSelection(selection, target);
    const started = new Date().toISOString();
    const state = {
      schema_version: 1, dataset_type: "openreview", venues: [], notes: [],
      raw_groups: [], raw_invitations: [], pending_public_forum: [], candidate_submissions: {},
      provenance: {
        fetched_at: started, exporter_version: 4, seed: 42,
        document_origin: root.location?.origin || "non_browser_test",
        selection_method: selection?.sampling_rule ||
          "Accepted public submissions; English title/abstract filter for LLM " +
          "inference efficiency; ascending SHA-256 of 42:<note_id>; first target submissions " +
          "with public reviews verified against group review_name and actual invitations. " +
          "Automatic topic selection requires manual audit before the final benchmark.",
        target_per_venue: target, status: "in_progress",
        topic_audit: selection ? "assistant_topic_selection_applied" : "pending_manual_review",
        topic_selection: selection,
        candidates: {}, exclusions: [], selected: [], requests: [], failed_requests: [],
      },
    };
    const collected = new Map();
    const inviteCache = new Map();

    async function get(path, params) {
      if (!["/groups", "/notes", "/invitations"].includes(path)) {
        throw new Error("Only the three read-only OpenReview endpoints are allowed.");
      }
      const url = new URL(path, API);
      for (const [key, value] of Object.entries(params).sort()) {
        url.searchParams.set(key, String(value));
      }
      if (cache.has(url.href)) {
        const saved = cache.get(url.href);
        state.provenance.requests.push({url: url.href, fetched_at: saved.fetched_at, cached: true});
        return saved.body;
      }
      for (let attempt = 0; attempt < 3; attempt++) {
        await sleep(250);
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 30000);
        try {
          const response = await transport(url.href, {
            method: "GET", credentials: "include", cache: "no-store", signal: controller.signal,
            headers: {Accept: "application/json"},
          });
          if (!response.ok) {
            let apiError = null;
            if (typeof response.json === "function") {
              try {apiError = await response.json();} catch (_) { /* Error page may be HTML. */ }
            }
            const errorName = typeof apiError?.name === "string" &&
              /^[A-Za-z][A-Za-z0-9_]{0,79}$/.test(apiError.name) ? apiError.name : null;
            state.provenance.failed_requests.push({
              url: url.href, status: response.status, error_name: errorName,
              fetched_at: new Date().toISOString(), attempt: attempt + 1,
            });
            const retryable = response.status === 429 || response.status >= 500;
            if (retryable && attempt < 2) {
              const delay = Number(response.headers.get("Retry-After")) || 2 ** (attempt + 1);
              clearTimeout(timeout);
              await sleep(Math.min(Math.max(delay, 1), 30) * 1000);
              continue;
            }
            if (response.status === 403) {
              throw new Error("OpenReview requires verification or denied access (403). " +
                "Stopped without retrying. Complete verification in the browser, then rerun.");
            }
            throw new Error(`OpenReview HTTP ${response.status}` +
              (errorName ? ` (${errorName})` : "") + `: ${path}. Export stopped.`);
          }
          const body = await response.json();
          if (!body || typeof body !== "object" || Array.isArray(body)) {
            throw new Error("Unexpected API response; export stopped.");
          }
          const fetched_at = new Date().toISOString();
          cache.set(url.href, {body, fetched_at});
          state.provenance.requests.push({url: url.href, fetched_at, cached: false});
          return body;
        } catch (error) {
          if ((error.name === "AbortError" || error instanceof TypeError) && attempt < 2) {
            clearTimeout(timeout);
            await sleep(2 ** (attempt + 1) * 1000);
            continue;
          }
          throw error;
        } finally {
          clearTimeout(timeout);
        }
      }
      throw new Error("Request retry limit reached.");
    }

    async function allNotes(params) {
      const notes = [];
      const seen = new Set();
      for (let page = 0; page < 100; page++) {
        const body = await get("/notes", {...params, limit: pageSize, offset: notes.length});
        if (!Array.isArray(body.notes)) throw new Error("API response has no notes list.");
        for (const note of body.notes) {
          if (!note.id || seen.has(note.id)) {
            throw new Error("Duplicate/missing note ID during pagination; export stopped.");
          }
          seen.add(note.id);
          notes.push(note);
        }
        if (Number.isInteger(body.count) && notes.length >= body.count) return notes;
        if (!body.notes.length || body.notes.length < pageSize) {
          if (Number.isInteger(body.count) && notes.length < body.count) {
            throw new Error("Incomplete API page; export stopped instead of truncating data.");
          }
          return notes;
        }
      }
      throw new Error("Pagination limit reached; no silent truncation.");
    }

    async function invitation(id) {
      if (inviteCache.has(id)) return inviteCache.get(id);
      // Historical review forms are closed; the API requires this explicit read filter.
      const body = await get("/invitations", {id, expired: true});
      const item = body.invitations?.find((entry) => entry.id === id);
      if (!item) throw new Error(`Cannot verify invitation ${id}.`);
      const fields = item.edit?.note?.content;
      state.raw_invitations.push(item);
      if (!fields || typeof fields !== "object" || Array.isArray(fields)) {
        throw new Error(`Review schema needs inspection: ${id}. Raw invitation saved in partial export.`);
      }
      inviteCache.set(id, item);
      return item;
    }

    async function orderKey(id) {
      const bytes = new TextEncoder().encode(`42:${id}`);
      const hash = await crypto.subtle.digest("SHA-256", bytes);
      return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, "0")).join("");
    }

    async function run() {
      try {
        progress("OpenReview exporter v4: " + (selection ? "topic-reviewed ID list." : "automatic topic filter."));
        for (const venueId of VENUES) {
          progress(`Loading conference configuration: ${venueId}`);
          const groups = await get("/groups", {id: venueId});
          const group = groups.groups?.find((item) => item.id === venueId);
          if (!group || group.domain !== venueId) throw new Error("Expected an API v2 venue group.");
          state.raw_groups.push({id: group.id, domain: group.domain, content: group.content});
          const submissionId = unwrap(group.content, "submission_id");
          const reviewName = unwrap(group.content, "review_name");
          if (typeof submissionId !== "string" || !submissionId.startsWith(venueId + "/") ||
              typeof reviewName !== "string" || !reviewName) {
            throw new Error("Missing venue submission_id or review_name; inspect group configuration.");
          }
          const venue = {
            id: venueId, year: 2024, submission_invitation: submissionId,
            verified: true, verification_note: "Group submission_id/review_name fetched via API v2. " +
              "Each imported review invitation is fetched by its exact ID; notes must be direct " +
              "public replies to the matching submission. Raw groups and schemas are included.",
            review_invitations: {}, rating_fields: [],
          };
          state.venues.push(venue);
          progress(`Loading accepted submission metadata: ${venueId}`);
          const accepted = await allNotes({"content.venueid": venueId, sort: "number:asc"});
          const requested = selection ? new Set(selection.venues[venueId]) : null;
          const candidates = accepted.filter((note) => publicNote(note) &&
            note.invitations?.includes(submissionId) &&
            (requested ? requested.has(note.id) : topicMatch(note)));
          state.candidate_submissions[venueId] = candidates;
          if (requested) {
            const available = new Set(candidates.map((note) => note.id));
            const missing = [...requested].filter((id) => !available.has(id));
            if (missing.length) {
              throw new Error("Topic-reviewed IDs unavailable among public accepted submissions: " +
                missing.join(", "));
            }
          }
          const ordered = await Promise.all(candidates.map(async (note) => ({
            note, key: await orderKey(note.id),
          })));
          ordered.sort((a, b) => a.key < b.key ? -1 : a.key > b.key ? 1 :
            (a.note.id < b.note.id ? -1 : a.note.id > b.note.id ? 1 : 0));
          state.provenance.candidates[venueId] = ordered.map(({note, key}) => ({
            id: note.id, title: unwrap(note.content, "title"), order_key: key,
          }));
          progress(`${venueId}: ${accepted.length} accepted, ${ordered.length} topic candidates.`);
          let selected = 0;
          for (const {note: submission} of ordered) {
            if (selected >= target) break;
            const forumNotes = await allNotes({forum: submission.forum});
            const publicNotes = forumNotes.filter(publicNote);
            state.pending_public_forum = publicNotes;
            const reviews = [];
            const verified = new Map();
            for (const reply of publicNotes) {
              if (reply.id === submission.id || reply.replyto !== submission.id ||
                  reply.forum !== submission.forum) continue;
              const ids = (reply.invitations || []).filter((id) =>
                id.startsWith(venueId + "/") && id.endsWith("/-/" + reviewName));
              if (!ids.length) continue;
              const fieldsForReply = new Set();
              for (const id of ids) {
                const schema = await invitation(id);
                if (schema.edit.note.replyto && typeof schema.edit.note.replyto === "string" &&
                    schema.edit.note.replyto !== submission.id) {
                  throw new Error("Invitation replyto does not match the submission.");
                }
                for (const field of ratingFields(schema.edit.note.content)) fieldsForReply.add(field);
                verified.set(id, schema);
              }
              const text = Object.entries(reply.content || {}).some(([field]) => {
                const raw = unwrap(reply.content, field);
                return !fieldsForReply.has(field) && typeof raw === "string" && raw.trim();
              });
              if (text) reviews.push(reply);
            }
            if (!reviews.length) {
              state.provenance.exclusions.push({id: submission.id, reason: "no_verified_public_review"});
              state.pending_public_forum = [];
              continue;
            }
            const reviewIds = new Set(reviews.flatMap((reply) => reply.invitations || []));
            for (const [id, schema] of verified) {
              if (!reviewIds.has(id)) continue;
              if (venue.review_invitations[id] && venue.review_invitations[id] !== submission.id) {
                throw new Error("The same review invitation points to two different submissions.");
              }
              venue.review_invitations[id] = submission.id;
              venue.rating_fields = [...new Set([
                ...venue.rating_fields, ...ratingFields(schema.edit.note.content),
              ])].sort();
            }
            collected.set(submission.id, submission);
            for (const note of publicNotes) collected.set(note.id, note);
            state.notes = [...collected.values()];
            state.pending_public_forum = [];
            selected++;
            state.provenance.selected.push({
              conference: venueId, id: submission.id, review_ids: reviews.map((reply) => reply.id),
            });
            progress(`${venueId}: ${selected}/${target}; ${unwrap(submission.content, "title")}`);
          }
          if (selected < target) {
            throw new Error(`${venueId}: only ${selected}/${target} eligible papers. ` +
              "Partial export saved; topic scope was not silently broadened.");
          }
        }
        state.provenance.status = selection ? "complete_with_topic_selection" : "complete_pending_topic_audit";
        state.provenance.completed_at = new Date().toISOString();
        return state;
      } catch (error) {
        state.provenance.status = "partial";
        state.provenance.error = error.message;
        state.provenance.stopped_at = new Date().toISOString();
        throw error;
      }
    }
    return {run, state, cache};
  }

  function save(snapshot, filename) {
    const blob = new Blob([JSON.stringify(snapshot, null, 2)], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }

  const exported = {createExporter, topicMatch, ratingFields};
  if (typeof module === "object" && module.exports) {
    module.exports = exported;
    return;
  }
  if (root.location?.origin !== WEBSITE) {
    console.error("Run this script on https://openreview.net/group?id=ICLR.cc/2024/Conference " +
      "while logged in. The API JSON viewer blocks script requests through its Content " +
      "Security Policy; do not run the exporter there.");
    return;
  }
  if (root.__openreviewExportRunning) {
    console.warn("An export is already running in this tab.");
    return;
  }
  root.__openreviewExportRunning = true;
  root.__openreviewExportCache ||= new Map();
  let exporter;
  try {
    exporter = createExporter({
      cache: root.__openreviewExportCache, selection: root.__openreviewTopicSelection ?? null,
    });
  } catch (error) {
    root.__openreviewExportRunning = false;
    console.error(error.message);
    return;
  }
  root.openreviewSnapshot = exporter.state;
  exporter.run().then((snapshot) => {
    const filename = snapshot.provenance.topic_selection ?
      "openreview-topic-reviewed.json" : "openreview-snapshot.json";
    save(snapshot, filename);
    console.log(`Saved ${filename}. Move it to data/raw/ in the project.`);
  }).catch((error) => {
    const filename = exporter.state.provenance.topic_selection ?
      "openreview-topic-partial.json" : "openreview-partial.json";
    save(exporter.state, filename);
    console.error(error.message);
    console.log("Saved partial data. Keep this tab open; successful requests are cached for rerun.");
  }).finally(() => {root.__openreviewExportRunning = false;});
})(globalThis);
