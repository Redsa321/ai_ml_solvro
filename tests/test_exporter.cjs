const assert = require("node:assert/strict");
const {webcrypto} = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const {test} = require("node:test");
const vm = require("node:vm");
const {fixtureApi} = require("./helpers/openreview_api.cjs");
const {createExporter, topicMatch, ratingFields} = require("../scripts/export-openreview.js");

function exporter(fake, overrides = {}) {
  return createExporter({
    fetch: fake.fetch, crypto: webcrypto, sleep: async () => {}, progress: () => {},
    targetPerVenue: 1, pageSize: 1, ...overrides,
  });
}

test("complete export is paginated, attributed, public and retains all official reviews", async () => {
  const fake = fixtureApi();
  fake.snapshot.notes.push({
    id: "private-review", forum: "fixture-neurips-cache", replyto: "fixture-neurips-cache",
    readers: ["private-reviewers"],
    invitations: ["NeurIPS.cc/2024/Conference/Submission1/-/Official_Review"],
    content: {review: {value: "PRIVATE: must not leave the browser"}},
  });
  const snapshot = await exporter(fake).run();
  assert.equal(snapshot.provenance.status, "complete_pending_topic_audit");
  assert.equal(snapshot.provenance.selected.length, 2);
  assert.equal(snapshot.venues.length, 2);
  assert(!JSON.stringify(snapshot).includes("PRIVATE: must not leave the browser"));
  for (const selected of snapshot.provenance.selected) {
    const expected = fake.snapshot.notes.filter((note) =>
      note.replyto === selected.id && note.readers.includes("everyone") &&
      note.invitations.some((id) => id.endsWith("/-/Official_Review")));
    assert.deepEqual(selected.review_ids.slice().sort(), expected.map((note) => note.id).sort());
    const venue = snapshot.venues.find((item) => item.id === selected.conference);
    for (const review of expected) {
      assert.equal(venue.review_invitations[review.invitations[0]], selected.id);
      assert(snapshot.raw_invitations.some((item) => item.id === review.invitations[0]));
    }
  }
  assert(fake.requests.every(({options}) => options.method === "GET"));
  assert(fake.requests.every(({options}) => options.credentials === "include"));
  assert(fake.requests.some(({url}) => Number(url.searchParams.get("offset")) > 0));
  assert(!fake.requests.some(({options}) => "Authorization" in options.headers));
  assert(fake.requests.filter(({url}) => url.pathname === "/invitations")
    .every(({url}) => url.searchParams.get("expired") === "true"));
  assert.deepEqual(snapshot.venues[1].rating_fields, ["confidence", "overall"]);
});

test("verification errors stop immediately and keep partial state", async () => {
  const fake = fixtureApi();
  let calls = 0;
  const client = exporter(fake, {fetch: async () => {
    calls++;
    return fake.reply(403, {name: "ChallengeRequiredError"});
  }});
  await assert.rejects(client.run(), /403/);
  assert.equal(calls, 1);
  assert.equal(client.state.provenance.status, "partial");
});

test("successful requests are reused after a later verification failure", async () => {
  const fake = fixtureApi();
  const cache = new Map();
  let failNextNotes = true;
  const fetch = async (url, options) => {
    if (new URL(url).pathname === "/notes" && failNextNotes) {
      failNextNotes = false;
      return fake.reply(403, {});
    }
    return fake.fetch(url, options);
  };
  await assert.rejects(exporter(fake, {cache, fetch}).run(), /403/);
  assert.equal(cache.size, 1);
  const resumed = await exporter(fake, {cache, fetch}).run();
  assert(resumed.provenance.requests.some((request) => request.cached));
  assert.equal(fake.requests.filter(({url}) => url.pathname === "/groups").length, 2);
});

test("rate limits retry within a bound; persistent server failure stops", async () => {
  const fake = fixtureApi();
  const delays = [];
  let calls = 0;
  const fetch = async (url, options) => {
    if (calls++ === 0) return fake.reply(429, {}, {"Retry-After": "1"});
    return fake.fetch(url, options);
  };
  await exporter(fake, {fetch, sleep: async (ms) => {delays.push(ms);}}).run();
  assert(delays.includes(1000));
  calls = 0;
  await assert.rejects(exporter(fake, {fetch: async () => {
    calls++;
    return fake.reply(503, {});
  }}).run(), /503/);
  assert.equal(calls, 3);
});

test("ignored offsets and truncated pages cannot silently lose submissions", async () => {
  const fake = fixtureApi();
  const ignoreOffset = async (url, options) => {
    const changed = new URL(url);
    changed.searchParams.set("offset", "0");
    return fake.fetch(changed.href, options);
  };
  await assert.rejects(exporter(fake, {fetch: ignoreOffset}).run(), /Duplicate/);
  const truncated = async (url, options) => {
    if (new URL(url).pathname === "/notes") return fake.reply(200, {count: 20, notes: []});
    return fake.fetch(url, options);
  };
  await assert.rejects(exporter(fake, {fetch: truncated}).run(), /Incomplete API page/);
});

test("a deficit keeps partial data instead of broadening the topic or inventing records", async () => {
  const fake = fixtureApi();
  const client = exporter(fake, {targetPerVenue: 2});
  await assert.rejects(client.run(), /only 1\/2 eligible papers/);
  assert.equal(client.state.provenance.status, "partial");
  assert.equal(client.state.provenance.selected.length, 3);
});

test("actual invitation relationship and schema are checked, not just the name", async () => {
  const fake = fixtureApi();
  const fetch = async (url, options) => {
    const response = await fake.fetch(url, options);
    if (new URL(url).pathname === "/invitations") {
      const body = await response.json();
      body.invitations[0].edit.note.replyto = "different-paper";
      return fake.reply(200, body);
    }
    return response;
  };
  await assert.rejects(exporter(fake, {fetch}).run(), /does not match/);
});

test("topic filtering excludes vision quantization and training-only distillation", () => {
  const note = (title, abstract) => ({content: {title: {value: title}, abstract: {value: abstract}}});
  assert(!topicMatch(note("Vision quantization", "We compress convolutional image classifiers.")));
  assert(!topicMatch(note("LLM distillation", "Knowledge distillation improves model training.")));
  assert(!topicMatch(note("Fine-Tuning Language Models for Factuality",
    "We improve factuality of large language models using preference rankings. " +
    "Our results improve over decoding strategies targeted at factuality.")));
  assert(topicMatch(note("KV cache compression for LLMs", "Memory-efficient inference.")));
});

test("rating fields come from original numeric scales rather than fixed conference names", () => {
  assert.deepEqual(ratingFields({
    custom_score: {value: {param: {type: "string", enum: ["1: poor", "5: strong"]}}},
    certainty: {value: {param: {type: "integer"}}},
    soundness: {value: {param: {type: "string", enum: ["1 poor", "3 good", "4 excellent"]}}},
    summary: {value: {param: {type: "string"}}},
    ethics: {value: {param: {enum: ["yes", "no"]}}},
  }), ["certainty", "custom_score", "soundness"]);
});

test("historical invitations require expired=true; the exporter retrieves the closed schema", async () => {
  const fake = fixtureApi();
  const id = Object.keys(fake.snapshot.venues[0].review_invitations)[0];
  const normal = await fake.fetch("https://api2.openreview.net/invitations?" +
    new URLSearchParams({id}), {method: "GET"});
  assert.equal(normal.status, 400);
  assert.equal((await normal.json()).name, "InvitationExpiredError");
  const snapshot = await exporter(fake).run();
  assert(snapshot.raw_invitations.length > 0);
  assert.equal(snapshot.provenance.failed_requests.length, 0);
});

test("API error name and failed request survive a partial export", async () => {
  const fake = fixtureApi();
  let calls = 0;
  const client = exporter(fake, {fetch: async () => {
    calls++;
    return fake.reply(400, {name: "InvitationExpiredError"});
  }});
  await assert.rejects(client.run(), /InvitationExpiredError/);
  assert.equal(calls, 1);
  assert.equal(client.state.provenance.failed_requests[0].error_name, "InvitationExpiredError");
  assert.equal(client.state.provenance.failed_requests[0].status, 400);
});

function topicSelection() {
  return {
    schema_version: 1, selection_type: "synthetic_test_selection", sampling_rule: "Test only",
    venues: {
      "ICLR.cc/2024/Conference": ["fixture-iclr-quant"],
      "NeurIPS.cc/2024/Conference": ["fixture-neurips-cache"],
    },
  };
}

test("an audited selection exports exactly its IDs and retains every public official review", async () => {
  const fake = fixtureApi();
  const selection = topicSelection();
  const paper = fake.snapshot.notes.find((note) => note.id === "fixture-iclr-quant");
  paper.content.title.value = "A fictional method selected by a reviewer";
  paper.content.abstract.value = "No automatic topic keywords occur here.";
  const snapshot = await exporter(fake, {selection}).run();
  assert.deepEqual(snapshot.provenance.selected.map((item) => item.id).sort(),
    Object.values(selection.venues).flat().sort());
  assert.equal(snapshot.provenance.status, "complete_with_topic_selection");
  assert.equal(snapshot.provenance.selected[0].review_ids.length, 2);
  assert.equal(snapshot.provenance.topic_audit, "topic_selection_applied");
});

test("a missing audited ID stops instead of substituting a different paper", async () => {
  const fake = fixtureApi();
  const selection = topicSelection();
  selection.venues["ICLR.cc/2024/Conference"] = ["not-available"];
  const client = exporter(fake, {selection});
  await assert.rejects(client.run(), /unavailable among public accepted submissions/);
  assert.equal(client.state.provenance.selected.length, 0);
});

test("invalid audited selections fail before network requests", () => {
  const fake = fixtureApi();
  const selection = topicSelection();
  selection.venues["NeurIPS.cc/2024/Conference"] = ["fixture-iclr-quant"];
  assert.throws(() => exporter(fake, {selection}), /duplicate or invalid/);
  assert.equal(fake.requests.length, 0);
});

function browserContext(origin) {
  const requests = [], errors = [], downloads = [], blobs = [];
  class BrowserURL extends URL {
    static createObjectURL(blob) {blobs.push(blob); return "blob:mock-download";}
    static revokeObjectURL() {}
  }
  const sandbox = {
    location: {origin}, crypto: webcrypto, AbortController, TextEncoder, Blob, URL: BrowserURL,
    console: {log() {}, warn() {}, error: (...args) => errors.push(args.join(" "))},
    fetch: async (url, options) => {
      requests.push({url, options});
      return {ok: false, status: 403};
    },
    setTimeout(callback, delay) {
      if (delay === 250) queueMicrotask(callback);
      return 1;
    },
    clearTimeout() {},
    document: {
      body: {appendChild() {}},
      createElement() {
        return {click() {downloads.push(this.download);}, remove() {}};
      },
      get cookie() {throw new Error("The exporter must not read browser cookies.");},
    },
  };
  const source = fs.readFileSync(path.join(__dirname, "../scripts/export-openreview.js"), "utf8");
  vm.runInNewContext(source, sandbox);
  return {sandbox, requests, errors, downloads, blobs};
}

test("browser entrypoint rejects the CSP-restricted API JSON viewer before any request", () => {
  const context = browserContext("https://api2.openreview.net");
  assert.equal(context.requests.length, 0);
  assert.equal(context.downloads.length, 0);
  assert(context.errors.some((message) => message.includes("https://openreview.net/group")));
  assert(context.errors.some((message) => message.includes("Content Security Policy")));
});

test("website entrypoint starts a credentialed API read and can save a diagnostic snapshot", async () => {
  const context = browserContext("https://openreview.net");
  for (let tick = 0; tick < 20 && context.sandbox.__openreviewExportRunning; tick++) {
    await new Promise((resolve) => setImmediate(resolve));
  }
  assert.equal(context.requests.length, 1);
  assert(context.requests[0].url.startsWith("https://api2.openreview.net/groups?"));
  assert.equal(context.requests[0].options.credentials, "include");
  assert.equal(context.requests[0].options.method, "GET");
  assert.deepEqual(context.downloads, ["openreview-partial.json"]);
  assert.equal(context.sandbox.__openreviewExportRunning, false);
  const snapshot = JSON.parse(await context.blobs[0].text());
  assert.equal(snapshot.provenance.document_origin, "https://openreview.net");
  assert.equal(snapshot.provenance.exporter_version, 4);
  assert.equal(snapshot.provenance.status, "partial");
  assert(context.errors.some((message) => message.includes("403")));
});
