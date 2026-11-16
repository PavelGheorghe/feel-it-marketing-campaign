/*
 * Import contacts into the Contacts list and attach them to a ContactLists audience.
 *
 * Usage (as a site member with edit rights):
 *   1. Open https://feelitservices.sharepoint.com/sites/Marketingcampaigns in the browser.
 *   2. Open DevTools > Console.
 *   3. Paste this whole file, then run:
 *        await importContacts("DACH Industrial Nov_Dec", rows)
 *      where rows = [{ Title, Email, FirstName, LastName, Company, JobTitle, Country, Phone, Language }, ...]
 *
 * The ContactLists row is created if it does not exist. Emails already in that audience are
 * skipped, so it is safe to re-run.
 */
async function importContacts(listName, rows, chunkSize = 20) {
  const web = window._spPageContextInfo?.webAbsoluteUrl
    || location.href.match(/^https:\/\/[^/]+\/sites\/[^/]+/)[0];
  const digest = await fetch(`${web}/_api/contextinfo`, {
    method: "POST", headers: { Accept: "application/json;odata=nometadata" }
  }).then(r => r.json()).then(j => j.FormDigestValue);

  const headers = {
    Accept: "application/json;odata=nometadata",
    "Content-Type": "application/json;odata=nometadata",
    "X-RequestDigest": digest
  };
  const api = list => `${web}/_api/web/lists/getbytitle('${list}')`;
  const getJson = async url => {
    const r = await fetch(url, { headers });
    if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
    return r.json();
  };

  // 1. Find or create the audience.
  const safeName = listName.replace(/'/g, "''");
  const found = await getJson(`${api("ContactLists")}/items?$select=Id,Title&$filter=Title eq '${encodeURIComponent(safeName)}'`);
  let listId = found.value[0]?.Id;
  if (!listId) {
    const r = await fetch(`${api("ContactLists")}/items`, {
      method: "POST", headers, body: JSON.stringify({ Title: listName })
    });
    if (!r.ok) throw new Error(`Create ContactLists row failed: ${r.status} ${await r.text()}`);
    listId = (await r.json()).Id;
  }

  // 2. Emails already in this audience.
  const existing = new Set();
  let next = `${api("Contacts")}/items?$select=Id,Email&$filter=ContactListId eq ${listId}&$top=500`;
  while (next) {
    const page = await getJson(next);
    page.value.forEach(i => existing.add((i.Email || "").trim().toLowerCase()));
    next = page["odata.nextLink"] || null;
  }

  // 3. Create the missing contacts.
  const todo = rows.filter(r => !existing.has(r.Email.trim().toLowerCase()));
  const failed = [];
  let created = 0;
  for (let i = 0; i < todo.length; i += chunkSize) {
    const chunk = todo.slice(i, i + chunkSize);
    await Promise.all(chunk.map(async row => {
      const r = await fetch(`${api("Contacts")}/items`, {
        method: "POST", headers, body: JSON.stringify({ ...row, ContactListId: listId })
      });
      if (r.ok) created++;
      else failed.push({ email: row.Email, status: r.status, error: (await r.text()).slice(0, 300) });
    }));
  }

  const result = { listId, created, skipped: rows.length - todo.length, failed };
  console.table([{ listId, created, skipped: result.skipped, failed: failed.length }]);
  if (failed.length) console.table(failed);
  return result;
}
