<!-- SPDX-License-Identifier: MPL-2.0 -->
# Visual design and asset handoff

Use for UI/UX, visual redesign, motion or assets that need engineering integration. Default to **Claude as designer**. An optional preference question can offer Codex-led design, but do not repeat a choice already made or block work waiting for this preference. Silence does not grant implementation, spending or deployment authorization.

## Design ownership

In Claude-designer mode the PM preserves the user's own words, use cases, information priorities, explicit preferences and hard constraints. Claude chooses research, available design tools, layout, typography, palette, motion and alternatives. PM suggestions must not become invented requirements or aesthetic acceptance gates. Check agreed usability, accessibility, data correctness, privacy and performance through observable evidence.

Only when the user chooses Codex-led design does Codex lead the visual brief and feedback. Claude still owns engineering decisions. Design ownership, asset production and permission to implement/deploy are separate fields. A design-only request returns the agreed artifact or prototype for assessment; it does not authorize full product delivery.

On a request to start over, replace superseded PM directions with the latest brief. Retain history and still-valid functional/data/authorization boundaries; do not delete prior work automatically. Use the original session for ordinary revisions. A fresh design session is appropriate when the user explicitly requests fresh context; record which prior design it supersedes and apply normal readiness/RC checks.

## Assets only when needed

Use the tools/skills actually available for the requested media; no private asset skill or particular image provider is required. A single image without integration needs no manifest workflow. Existing vector/programmatic art need not become raster art. If a required tool is unavailable, report the asset gap and continue independent engineering work.

For coordinated asset sets:

- Name the designer, asset producer and engineering consumer. Assign each writable path one owner. The PM may produce explicitly assigned assets while Claude implements, using the designer's brief; this does not grant product-code ownership or design authority.
- Stage assets outside Claude's writable product paths. Publish an immutable **READY revision** with IDs, file paths, versions/hashes, dimensions, transparency and relevant crop/anchor/frame metadata. Draft/blockout art stays labeled as such.
- Claude records the consumed revision and each asset's ID/hash/destination. Verify hashes after copying into durable project paths. Derived files identify their source and transformation. Keep receipt/integration status separate from the immutable manifest.
- Changed pixels require rechecking affected crop/anchor metadata. Report defects with asset ID, role, orientation, display size, current revision and screenshot/measurement; publish a new revision instead of silently replacing files.
- Freeze the actual consumed combination for runtime screenshots/video and applicable project gates. Revalidate affected scenarios when it changes. **READY**, **INTEGRATED** and **ACCEPTED** are distinct outcomes; a generated image alone is not runtime acceptance.

Record only applicable fields in the mission/handoff. This procedure adds no asset requirement to ordinary backend work.
