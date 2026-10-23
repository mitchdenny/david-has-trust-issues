# david-has-trust-issues

A public GitHub template and unpacked .NET template for an Aspire **TypeScript
AppHost**, **Express API**, and **React/Vite frontend**. No Azure resources or cloud
provisioning are configured.

## Generate an app

With the custom Aspire CLI that supports Git template repositories:

```bash
aspire new --template-repository git@github.com:mitchdenny/david-has-trust-issues.git
```

The custom CLI asks for the project name and injects its active `AspireVersion` and
raw identity-channel `AspireNuGetSource` when these well-known parameters are
declared. The repository contains exactly one template.

SSH Git URLs require a GitHub SSH key even for this public repository. HTTPS avoids
that requirement:

```bash
aspire new --template-repository https://github.com/mitchdenny/david-has-trust-issues.git
```

A local clone also works with the custom CLI:

```bash
git clone https://github.com/mitchdenny/david-has-trust-issues.git
aspire new --template-repository ./david-has-trust-issues
```

The stock Aspire CLI used to create this scaffold does **not** yet expose
`--template-repository`. Use the custom CLI above, or stock .NET templating:

```bash
git clone https://github.com/mitchdenny/david-has-trust-issues.git
dotnet new install ./david-has-trust-issues
dotnet new david-has-trust-issues --name Contoso.Inventory --output ./Contoso.Inventory
```

Both injected parameters are optional for stock `dotnet new`. Defaults are
`17.0.0-preview.1.26520.10` and the public Aspire daily feed
`https://pkgs.dev.azure.com/dnceng/public/_packaging/aspire-dev/nuget/v3/index.json`.
To use a different matching SDK/channel:

```bash
dotnet new david-has-trust-issues --name MyApp --output ./MyApp \
  --AspireVersion YOUR_ASPIRE_VERSION \
  --AspireNuGetSource YOUR_FEED_URL_OR_LOCAL_DIRECTORY
```

Pass the feed as a raw URL/path, not XML-escaped text. The template escapes XML
attributes (including quotes), keeps NuGet source/mapping keys static, and replaces
both SDK and hosting package versions. The scaffold's `daily` channel is preserved;
select a compatible Aspire CLI and feed for any overridden version.

The AppHost, `api`, and `frontend` paths are deliberately generic and do not require
project-derived filename renames. Project-derived npm names are lowercased and
sanitized consistently in manifests and lockfiles: `Contoso.Inventory` becomes
`contoso.inventory`, while `david-has-trust-issues` retains its hyphens.

GitHub's **Use this template** copies the repository itself, including its template
authoring metadata; use Aspire/.NET generation above for a clean, named application.

## Prerequisites and generated-app lifecycle

- An Aspire CLI compatible with the selected SDK version.
- .NET SDK 10 or newer, as required by that Aspire CLI.
- Node.js `^20.19.0`, `^22.13.0`, or `>=24`, with npm.
- Git for repository generation. Docker is only needed for container publishing or
  if you subsequently add container-backed resources.

Inside a generated application:

```bash
aspire restore --apphost apphost.mts --non-interactive
aspire start --apphost apphost.mts --isolated --non-interactive
aspire wait frontend --apphost apphost.mts --timeout 120 --non-interactive
aspire describe --apphost apphost.mts
aspire stop --apphost apphost.mts --non-interactive
```

`aspire run --apphost apphost.mts` is the foreground alternative. Aspire generates
`.aspire/modules` and installs npm dependencies; do not edit generated modules.
This preview starter has fixed dashboard/resource-service ports in its profiles.
The scaffold CLI retained those ports even with `--isolated` during smoke tests;
run generated apps serially or configure distinct profile ports for concurrent runs.
The frontend proxies `/api` to the API endpoint supplied by Aspire. The API exposes
`/health` and `/api/weatherforecast`; telemetry goes to the local Aspire dashboard.
The upstream starter also supports bundling frontend output into the API container
when publishing, but this template does not provision a deployment.

After dependency restore, checks can also be run explicitly:

```bash
npm ci
npm run build
npm --prefix api ci
npm --prefix api run build
npm --prefix frontend ci
npm --prefix frontend run build
npm --prefix frontend run lint
```

## Template development

Scaffold provenance:

```bash
# Aspire CLI 17.0.0-preview.1.26520.10
aspire new aspire-ts-starter --name TemplateApp --output .scaffold \
  --non-interactive --suppress-agent-init
```

The starter's resource wiring is preserved. Its OpenTelemetry log processor call
is updated to match the scaffold's dependency API; the API also has an explicit
TypeScript build/check script and lockfile. Generated modules,
dependencies, build output, local state/secrets, Git metadata, this repository's
README, and generation tests are excluded from instantiated applications.

Run the lightweight generation regressions with Python 3 and the .NET SDK:

```bash
python3 tests/generation.py
```

This uses an isolated template hive under ignored `.validation/` and generates both
required names, plus version/feed override cases. It checks npm/lock consistency,
generic paths/references, XML round-tripping, version replacement, and exclusions.
Each run recreates its four generated application folders under `.validation/`;
do not keep work in those disposable folders.
It does not exercise the custom CLI's repository transport; that CLI is not included
in this repository.
