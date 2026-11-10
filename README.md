# Feel IT – Marketing campaigns (Brevo replacement)

Email campaigns sent from **your own Outlook mailbox** by a Power Automate flow. Contacts, templates and the send log are stored in SharePoint lists on
[Marketingcampaigns](https://feelitservices.sharepoint.com/sites/Marketingcampaigns).

## The lists

| List | What goes in it |
|---|---|
| **ContactLists** | One row per audience, e.g. "MANUFACTURERS DE ARINA" |
| **Contacts** | One row per person per audience. Title = full name. Set **ContactList** to the audience. |
| **EmailTemplates** | Subject + **HtmlBody** (raw HTML). Untick **Active** to retire a template. |
| **Senders** | One row per colleague: your **Email** and **SignatureHtml** |
| **Campaigns** | One row per campaign. Its **ID** is what you type when you run the flow. |
| **CampaignSends** | Filled by the flow: who got which campaign, when, and whether they replied |
| **Suppression** | Never email these addresses (unsubscribes, bounces, blocklist) |

### Template placeholders
`{{FirstName}} {{LastName}} {{Company}} {{JobTitle}} {{Email}} {{SenderName}} {{Signature}}`

Brevo syntax also works: `{{ contact.FIRSTNAME }}`, `{{ contact.LASTNAME }}`, `{{ contact.COMPANY_NAME }}`.
Images (logo, signature photo) must use a **public https URL**. Recipients can't see SharePoint images.
End every template with an unsubscribe line, e.g. *„Antworten Sie mit ABMELDEN“*.

## Running a campaign

1. **Contacts:** import them into **Contacts** (Excel/CSV: `templates/contacts-import-sample.csv`, or the list's grid view) and set **ContactList** on each row.
2. **Campaign row:** create it in **Campaigns** with Title, Template, ContactList, BatchSize (default 200), DelaySeconds (default 5) and TestEmail. Note its **ID**.
3. **Test:** run the **Marketing campaign** flow with Campaign ID = the ID and Mode = **Test**. You get one `[TEST]` email.
4. **Send:** run it again with Mode = **Send**. It sends the next batch from your mailbox and logs every email in CampaignSends.
5. **Next batch:** run Send again. Anyone already emailed by this campaign is skipped automatically. When everyone has been emailed, Status becomes **Completed**.
6. **Pause:** set the campaign's Status to **Paused** in SharePoint. The flow stops after the current email. Run Send again to resume.

**Status** and **LastRunMessage** on the campaign row show what happened in the last run.

### Follow-up to non-repliers
1. Run **Marketing campaign - Sync replies** with the original campaign's ID. It marks who replied, and replies containing ABMELDEN / unsubscribe / dezabonare go into **Suppression**.
2. Create a new campaign row:
   - **CampaignType** = *Follow-up non-repliers*
   - **ParentCampaignNo** = the original campaign's ID
   - **ContactList** = the same audience as the original
   - **Template** = your follow-up template
3. Test, then Send, as above.

### Limits
- Exchange Online allows about 30 emails/min and 10,000 recipients/day per mailbox. The defaults stay far below that. Keep cold outreach to a few hundred per day per person.
- There is no open or click tracking (Standard licence). Follow-ups are based on replies.

## For admins

| Path | What it is |
|---|---|
| `sharepoint/site-script.json`, `indexes.json`, `apply-site-script.js` | List definitions + provisioning (run in the browser console as a site owner) |
| `flows/*/definition.json` | The flow definitions (source of truth) |
| `flows/build_solution.py` | Builds `flows/dist/FeelITMarketingCampaign_<version>.zip`. Import it at make.powerapps.com → Solutions → Import solution. Bump `VERSION` for updates. |
| `flows/build_packages.py` | Legacy import packages. The legacy importer hung in our tenant, so use the solution. |
| `templates/` | Sample German template, signature and contact CSV |

**Sharing with colleagues:**
1. Open the flow → **Run only users** → add people.
2. Set **Office 365 Outlook = Provided by run-only user** so mail is sent from their mailbox.
3. Keep **SharePoint** on the owner's connection.
4. Add a **Senders** row for each colleague.
