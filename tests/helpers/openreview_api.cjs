// Local fake API for exporter behavior tests. No requests to the real service.
const fs = require("node:fs");
const path = require("node:path");

function fixtureApi() {
  const snapshot = JSON.parse(fs.readFileSync(
    path.join(__dirname, "../fixtures/synthetic_snapshot.json"), "utf8",
  ));
  const requests = [];
  function reply(status, body, headers = {}) {
    return {
      ok: status >= 200 && status < 300, status,
      headers: {get: (key) => headers[key] ?? null},
      json: async () => structuredClone(body),
    };
  }
  async function fetch(urlText, options) {
    const url = new URL(urlText);
    requests.push({url, options});
    const venue = snapshot.venues.find((item) => item.id === url.searchParams.get("id"));
    if (url.pathname === "/groups" && venue) {
      return reply(200, {groups: [{
        id: venue.id, domain: venue.id,
        content: {submission_id: {value: venue.submission_invitation},
          review_name: {value: "Official_Review"}},
      }]});
    }
    if (url.pathname === "/invitations") {
      if (url.searchParams.get("expired") !== "true") {
        return reply(400, {name: "InvitationExpiredError"});
      }
      const id = url.searchParams.get("id");
      const owner = snapshot.venues.find((item) => item.review_invitations[id]);
      if (!owner) return reply(404, {});
      const content = {summary: {value: {param: {type: "string"}}}};
      for (const field of owner.rating_fields) {
        const scale = field === "overall" ? ["1 poor", "4 excellent"] : ["1: low", "4: high"];
        content[field] = {value: {param: {type: "string", enum: scale}}};
      }
      return reply(200, {invitations: [{id, edit: {note: {
        replyto: owner.review_invitations[id], content,
      }}}]});
    }
    if (url.pathname === "/notes") {
      const conference = url.searchParams.get("content.venueid");
      const forum = url.searchParams.get("forum");
      const notes = snapshot.notes.filter((note) => conference
        ? note.content.venueid?.value === conference : note.forum === forum);
      const offset = Number(url.searchParams.get("offset") || 0);
      const limit = Number(url.searchParams.get("limit") || 500);
      return reply(200, {count: notes.length, notes: notes.slice(offset, offset + limit)});
    }
    return reply(404, {});
  }
  return {fetch, snapshot, requests, reply};
}

module.exports = {fixtureApi};
