/*
 * Provision the marketing-campaign lists on a SharePoint site.
 *
 * Usage (as a site owner):
 *   1. Open https://feelitservices.sharepoint.com/sites/Marketingcampaigns in the browser.
 *   2. Open DevTools > Console.
 *   3. Paste this whole file, then run:
 *        await provision(<contents of site-script.json>, <contents of indexes.json>)
 *
 * The site script is executed with SiteScriptUtility.ExecuteTemplateScript (same engine as
 * "Apply a site template"). Afterwards the columns in indexes.json are indexed through REST,
 * because a site script cannot index a lookup column. It is safe to re-run: existing lists and
 * fields are left as they are.
 */
async function provision(siteScript, indexes) {
  const web = _spPageContextInfo.webAbsoluteUrl;
  const digest = await fetch(`${web}/_api/contextinfo`, {
    method: "POST", headers: { Accept: "application/json;odata=nometadata" }
  }).then(r => r.json()).then(j => j.FormDigestValue);

  const headers = {
    Accept: "application/json;odata=nometadata",
    "Content-Type": "application/json;odata=nometadata",
    "X-RequestDigest": digest
  };

  const res = await fetch(
    `${web}/_api/Microsoft.Sharepoint.Utilities.WebTemplateExtensions.SiteScriptUtility.ExecuteTemplateScript()`,
    { method: "POST", headers, body: JSON.stringify({ script: JSON.stringify(siteScript) }) }
  );
  const result = await res.json();
  if (!res.ok) throw new Error(JSON.stringify(result));
  const outcomes = (result.value || []).map(a => `${a.Title} -> ${a.OutcomeText || a.Outcome}`);
  console.table(outcomes);

  const indexed = [];
  for (const [list, fields] of Object.entries(indexes)) {
    for (const field of fields) {
      const r = await fetch(
        `${web}/_api/web/lists/getbytitle('${list}')/fields/getbyinternalnameortitle('${field}')`,
        { method: "POST", headers: { ...headers, "X-HTTP-Method": "MERGE", "IF-MATCH": "*" },
          body: JSON.stringify({ Indexed: true }) }
      );
      indexed.push(`${list}.${field}: ${r.ok ? "indexed" : "FAILED " + r.status}`);
    }
  }
  console.table(indexed);
  return { outcomes, indexed };
}
