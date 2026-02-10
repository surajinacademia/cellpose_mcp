# License compliance summary

This document summarizes how **cellpose-mcp** complies with the licenses of the software it uses and distributes.

## Your license: BSD-3-Clause

- **Your code**: All original code in this repository is under **BSD-3-Clause** (see [LICENSE](LICENSE)).
- **pyproject.toml**: Correctly states `license = {text = "BSD-3-Clause"}` and the classifier `License :: OSI Approved :: BSD License`.
- **README**: Correctly states "BSD-3-Clause License" and links to the LICENSE file.

## Cellpose (Howard Hughes Medical Institute)

- **Cellpose license**: [BSD-3-Clause](https://github.com/MouseLand/cellpose/blob/main/LICENSE) (Copyright © 2020 Howard Hughes Medical Institute).
- **How you use it**: You use Cellpose only as a **library dependency** (e.g. `from cellpose import io, models`). You do **not** copy or redistribute Cellpose’s source code inside this repo.
- **What you must do** (and have done):
  1. **Retain copyright notice** – You list "Copyright (c) 2020, Howard Hughes Medical Institute (Cellpose)" in [LICENSE](LICENSE). ✅
  2. **Retain the BSD conditions and disclaimer** – Your LICENSE contains the full BSD-3-Clause text. ✅
  3. **No endorsement without permission** – Your LICENSE includes the clause that neither the names of the copyright holders nor their contributors may be used to endorse or promote products without permission. ✅

**Conclusion**: Your use of Cellpose (as a dependency only) and your LICENSE file are compliant with Cellpose’s BSD-3-Clause terms.

## Napari-MCP (inspiration)

- **Napari-MCP**: [BSD-3-Clause](https://github.com/royerlab/napari-mcp); you describe the project as “inspired by” napari-mcp.
- You do **not** copy napari-mcp source code; you only took inspiration from the idea. There is no obligation to add their copyright to your LICENSE.
- You already give attribution in the README under **Acknowledgments**. ✅

## Other dependencies

You depend on: **fastmcp**, **cellpose**, **numpy**, **imageio**, **tifffile**, **typer**, **rich** (and optional test/dev tools). These are used only as installed libraries; you do not ship their source code. Their licenses (BSD, MIT, etc.) allow this use. You are not required to list each dependency’s license in your LICENSE file; keeping your own LICENSE and this compliance note is sufficient.

## Checklist

| Requirement | Status |
|------------|--------|
| Your project has a clear LICENSE (BSD-3-Clause) | ✅ |
| LICENSE is included in the package (MANIFEST.in) | ✅ |
| Cellpose/HHMI copyright and conditions retained | ✅ |
| No endorsement clause present and applies to all copyright holders | ✅ |
| README mentions license and points to LICENSE | ✅ |
| Only use Cellpose as a dependency (no copied code) | ✅ |
| Napari-MCP credited in README (no code copied) | ✅ |

## Disclaimer

This summary is for project documentation only and does not constitute legal advice. For definitive guidance, consult a lawyer or your institution’s legal office.
