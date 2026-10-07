# Public documentation and maintenance policy

- HayosoAi is the public-facing identity. Describe projects and results without personal names, personal bylines, biographical framing, or identifying labels for the individual directing the work.
- Omit disclosures about which authoring, coding, translation, organization, or review tools produced the work. Keep substantive discussion of the software’s runtime models, experiments, and research subject.
- State demonstrated results, tested domains, and unresolved questions precisely. Replace repetitive defensive boilerplate with concise affirmative scope; never broaden a claim.
- Preserve licenses, copyright notices, third-party attribution, source/data rights, factual reproduction provenance, and externally required publication or competition disclosures. Flag uncertain external requirements for review before altering them.
- Edit sources before generated material. Regenerate current inventories after changes. Preserve historical evidence, upstream snapshots, Git history, and existing releases.
- Use relative repository links where possible. Obtain clone URLs from the repository interface; do not invent a replacement hosting identity or URL.
- Review public text, metadata, templates, and generated artifacts before publication. Quoted sources and ordinary first-person arguments retain their meaning.

## Project checks

Follow `REPRODUCE.md` for scientific reproduction. Editorial changes must preserve measured source code, patches, original datasets, and result files unless a separately documented experiment changes them.

Regenerate current manifests with `python tools/update_manifest.py`, then verify with `python tools/update_manifest.py --check`. Keep `FROZEN_PUBLICATION_MANIFEST.json` and `FROZEN_PUBLICATION_SHA256SUMS` byte-for-byte: their paths and digests describe the historical publication, including filenames later replaced in the current presentation.

Preserve `baseline/CONTRIBUTING.md`, `baseline/pull_request_template.md`, upstream MIT notices, and CC BY-NC 4.0 attribution. These external requirements and original source/data records are distinct from this repository’s public presentation policy.

Keep the finite-coordinate/sentinel domain, tested OpenCV/platform coverage, three-patch real-data scope, native coordinate units, and unresolved thread-configuration discrepancy explicit.
