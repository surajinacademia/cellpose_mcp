# Security Policy

## Supported Versions

Security fixes are provided for the latest release.

| Version | Supported |
| --- | --- |
| 0.1.5 | Yes |
| 0.1.4 and earlier | No |

## Reporting a Vulnerability

Do not open a public issue for an undisclosed vulnerability. Email `ssahu2@ucmerced.edu` with the affected version, reproduction steps, impact, and any suggested mitigation. You should receive an acknowledgment within seven days.

## Trust Model

Cellpose-MCP runs locally over stdio with the permissions of the current user. It can read requested images and replace requested output files. Use it only with trusted MCP clients and review agent-requested paths before approving sensitive work.

The package does not upload image bytes. Cellpose may download pretrained weights from the official Cellpose model host, and the connected AI client may separately transmit prompts, paths, metadata, or tool results according to that client's policy.

`.npy` input and arbitrary local model paths are not accepted. Use TIFF or PNG inputs and a model identifier reported by `cellpose-mcp-cli models`.
