"""Build an unmanaged Dataverse solution (.zip) containing both flows.

Usage:  python3 flows/build_solution.py
Output: flows/dist/FeelITMarketingCampaign_1_0_0_0.zip
Import: Power Automate > Solutions > Import solution > Browse > select the zip > Next >
        pick your SharePoint and Office 365 Outlook connections > Import.

Office 365 Outlook uses runtimeSource "invoker". That means "provided by run-only user": mail
is sent from the mailbox of the colleague who runs the flow.
"""
import json
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
DIST = HERE / "dist"
VERSION = "1.0.0.0"
PREFIX = "feelit"

FLOWS = [
    ("marketing-campaign", "Marketing campaign"),
    ("marketing-campaign-sync-replies", "Marketing campaign - Sync replies"),
]
CONNREFS = {
    "shared_sharepointonline": {"logical": f"{PREFIX}_sharedsharepointonline_mc", "display": "SharePoint (Marketing campaign)",
                                "runtime": "embedded"},
    "shared_office365": {"logical": f"{PREFIX}_sharedoffice365_mc", "display": "Office 365 Outlook (Marketing campaign)",
                         "runtime": "invoker"},
}


def wf_id(folder: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "feel-it/solution/" + folder)).upper()


def workflow_json(folder: str) -> str:
    definition = json.loads((HERE / folder / "definition.json").read_text())
    refs = {key: {"runtimeSource": c["runtime"],
                  "connection": {"connectionReferenceLogicalName": c["logical"]},
                  "api": {"name": key}} for key, c in CONNREFS.items()}
    return json.dumps({"properties": {"connectionReferences": refs, "definition": definition},
                       "schemaVersion": "1.0.0.0"}, indent=2, ensure_ascii=False)


def file_name(folder: str, name: str) -> str:
    return "".join(ch for ch in name if ch.isalnum()) + f"-{wf_id(folder)}.json"


def customizations() -> str:
    workflows = []
    for folder, name in FLOWS:
        workflows.append(f"""    <Workflow WorkflowId="{{{wf_id(folder).lower()}}}" Name="{escape(name)}">
      <JsonFileName>/Workflows/{file_name(folder, name)}</JsonFileName>
      <Type>1</Type>
      <Subprocess>0</Subprocess>
      <Category>5</Category>
      <Mode>0</Mode>
      <Scope>4</Scope>
      <OnDemand>0</OnDemand>
      <TriggerOnCreate>0</TriggerOnCreate>
      <TriggerOnDelete>0</TriggerOnDelete>
      <AsyncAutodelete>0</AsyncAutodelete>
      <SyncWorkflowLogOnFailure>0</SyncWorkflowLogOnFailure>
      <StateCode>1</StateCode>
      <StatusCode>2</StatusCode>
      <RunAs>1</RunAs>
      <IsTransacted>1</IsTransacted>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <IsCustomizable>1</IsCustomizable>
      <BusinessProcessType>0</BusinessProcessType>
      <IsCustomProcessingStepAllowedForOtherPublishers>1</IsCustomProcessingStepAllowedForOtherPublishers>
      <PrimaryEntity>none</PrimaryEntity>
      <LocalizedNames>
        <LocalizedName languagecode="1033" description="{escape(name)}" />
      </LocalizedNames>
    </Workflow>""")
    connrefs = []
    for key, c in CONNREFS.items():
        connrefs.append(f"""    <connectionreference connectionreferencelogicalname="{c['logical']}">
      <connectionreferencedisplayname>{escape(c['display'])}</connectionreferencedisplayname>
      <connectorid>/providers/Microsoft.PowerApps/apis/{key}</connectorid>
      <iscustomizable>1</iscustomizable>
      <promptingbehavior>0</promptingbehavior>
      <statecode>0</statecode>
      <statuscode>1</statuscode>
    </connectionreference>""")
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.0.0" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.0.0">
  <Entities />
  <Roles />
  <Workflows>
{chr(10).join(workflows)}
  </Workflows>
  <FieldSecurityProfiles />
  <Templates />
  <EntityMaps />
  <EntityRelationships />
  <OrganizationSettings />
  <optionsets />
  <CustomControls />
  <EntityDataProviders />
  <connectionreferences>
{chr(10).join(connrefs)}
  </connectionreferences>
  <Languages>
    <Language>1033</Language>
  </Languages>
</ImportExportXml>
"""


def solution() -> str:
    roots = "\n".join(f'      <RootComponent type="29" id="{{{wf_id(f).lower()}}}" behavior="0" />' for f, _ in FLOWS)
    address = """        <Address>
          <AddressNumber>{n}</AddressNumber>
          <AddressTypeCode>1</AddressTypeCode>
          <City xsi:nil="true"></City>
          <County xsi:nil="true"></County>
          <Country xsi:nil="true"></Country>
          <Fax xsi:nil="true"></Fax>
          <FreightTermsCode xsi:nil="true"></FreightTermsCode>
          <ImportSequenceNumber xsi:nil="true"></ImportSequenceNumber>
          <Latitude xsi:nil="true"></Latitude>
          <Line1 xsi:nil="true"></Line1>
          <Line2 xsi:nil="true"></Line2>
          <Line3 xsi:nil="true"></Line3>
          <Longitude xsi:nil="true"></Longitude>
          <Name xsi:nil="true"></Name>
          <PostalCode xsi:nil="true"></PostalCode>
          <PostOfficeBox xsi:nil="true"></PostOfficeBox>
          <PrimaryContactName xsi:nil="true"></PrimaryContactName>
          <ShippingMethodCode>1</ShippingMethodCode>
          <StateOrProvince xsi:nil="true"></StateOrProvince>
          <Telephone1 xsi:nil="true"></Telephone1>
          <Telephone2 xsi:nil="true"></Telephone2>
          <Telephone3 xsi:nil="true"></Telephone3>
          <TimeZoneRuleVersionNumber xsi:nil="true"></TimeZoneRuleVersionNumber>
          <UPSZone xsi:nil="true"></UPSZone>
          <UTCOffset xsi:nil="true"></UTCOffset>
          <UTCConversionTimeZoneCode xsi:nil="true"></UTCConversionTimeZoneCode>
        </Address>"""
    return f"""<?xml version="1.0" encoding="utf-8"?>
<ImportExportXml version="9.2.0.0" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.0.0" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.0.0">
  <SolutionManifest>
    <UniqueName>FeelITMarketingCampaign</UniqueName>
    <LocalizedNames>
      <LocalizedName description="Feel IT Marketing Campaign" languagecode="1033" />
    </LocalizedNames>
    <Descriptions>
      <Description description="Brevo replacement: SharePoint lists + manual campaign flows." languagecode="1033" />
    </Descriptions>
    <Version>{VERSION}</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>feelitservices</UniqueName>
      <LocalizedNames>
        <LocalizedName description="Feel IT Services" languagecode="1033" />
      </LocalizedNames>
      <Descriptions />
      <EMailAddress xsi:nil="true"></EMailAddress>
      <SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
      <CustomizationPrefix>{PREFIX}</CustomizationPrefix>
      <CustomizationOptionValuePrefix>33470</CustomizationOptionValuePrefix>
      <Addresses>
{address.format(n=1)}
{address.format(n=2)}
      </Addresses>
    </Publisher>
    <RootComponents>
{roots}
    </RootComponents>
    <MissingDependencies />
  </SolutionManifest>
</ImportExportXml>
"""


CONTENT_TYPES = ('<?xml version="1.0" encoding="utf-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension="xml" ContentType="application/octet-stream" />'
                 '<Default Extension="json" ContentType="application/octet-stream" /></Types>')

if __name__ == "__main__":
    DIST.mkdir(exist_ok=True)
    out = DIST / f"FeelITMarketingCampaign_{VERSION.replace('.', '_')}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CONTENT_TYPES)
        z.writestr("solution.xml", solution())
        z.writestr("customizations.xml", customizations())
        for folder, name in FLOWS:
            z.writestr(f"Workflows/{file_name(folder, name)}", workflow_json(folder))
    print("built", out.relative_to(HERE.parent))
