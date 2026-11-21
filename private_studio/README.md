# Owner setup
Keep the public site on GitHub Pages. Before merging, deploy this repository to an HTTPS Python host with persistent private storage at studio.maniteja.me. With the repository root as the working directory install private_studio/requirements.txt and run gunicorn private_studio.app:app. Mount an owner-only persistent directory outside the checkout for the SQLite database. Back up that volume privately.

Create a GitHub OAuth app owned by manitejakun. Use https://studio.maniteja.me for its homepage and https://studio.maniteja.me/callback for its callback. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in your host's secret settings. Set SESSION_SECRET to a generated random secret of at least 32 bytes, STUDIO_DATABASE to the absolute private database filename, and PUBLISH_KEY to a fine-grained GitHub token limited to this repository with Contents read/write. Configure HTTPS and the studio subdomain after owner approval. No secrets belong in GitHub files.

# Writing
From Journal choose Write an entry and sign in to GitHub. Select New entry, type a title, and press Enter for another block or Shift+Enter for a line break. Use the block menu for headings, quotes, lists and links. Under Publication details choose an optional cover file, alt text and caption. Wait for the saved state. Preview uses the article template. Select Back to draft to resume. Publish commits the entry and optional photo together. Follow Check deployment and verify the title on the homepage, Journal, and /journal/your-slug/. The Open an entry menu includes private drafts and published entries. A concurrent content change causes a conflict and preserves the draft.

The prior browser-only studio's device drafts stay in that browser. Export or copy any unfinished entry before switching.
