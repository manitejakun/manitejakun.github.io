# Mani Teja — Personal Portfolio

A static, GitHub Pages-ready personal portfolio closely following the typography, dimensions, timeline, and sections of https://uhvardhan.github.io/.

## Files

- `index.html` — all visible text, social links, sections, and timeline items
- `style.css` — exact-style layout measurements and mobile adjustments
- `script.js` — automatic copyright year
- `images/profile.svg` — **placeholder** profile image; replace it with your own
- `images/experience.svg`, `project.svg`, `education.svg` — **placeholder** timeline logos; replace with real institution/company logos if appropriate
- `images/favicon.svg` — small browser-tab icon
- `CNAME` — the custom domain `maniteja.me`
- `.nojekyll` — tells GitHub Pages to serve these files directly

## Customize before publishing

1. Open `index.html` and replace the tagline, bio, timeline placeholders, project/publication entries, and email/social links with your actual details. **Nothing marked as a placeholder is a claim about your biography.**
2. Replace `images/profile.svg` with an actual portrait file and change the image `src` in `index.html` to match (e.g. `images/me.jpg`).
3. Replace example timeline logos with your college/company logos and update their `src` paths.
4. The demo email `hello@maniteja.me` will work **only if you have configured an actual email mailbox** for it. Change or remove it if not.
5. Optionally add `docs/resume.pdf` and a link for your CV in the social links header.

## Deploy through GitHub Pages

1. Create a new **public** GitHub repository named exactly `<YOUR-GITHUB-USERNAME>.github.io` (using your *actual* GitHub username). If you already have that repository, use it.
2. Upload the **contents** of this folder to the repository root, including `index.html`, `style.css`, `images/`, `CNAME`, and `.nojekyll`. Do not upload only the ZIP or put everything inside an extra enclosing folder.
3. In the repo, open **Settings → Pages → Build and deployment**, choose **Deploy from a branch**, then **main** and **/(root)**. Save.
4. Verify the site works at `https://<YOUR-GITHUB-USERNAME>.github.io/`.
5. In **Settings → Pages**, enter `maniteja.me` as the custom domain if GitHub hasn't already picked it up from `CNAME`.
6. At Namecheap DNS management, configure the apex domain `@` with these four **A** records (replace conflicting A records):
   - `185.199.108.153`
   - `185.199.109.153`
   - `185.199.110.153`
   - `185.199.111.153`
   Optionally set `www` CNAME pointing to `<YOUR-GITHUB-USERNAME>.github.io` (without `https://`). Avoid conflicting www records.
7. Once DNS/HTTPS are ready, enable **Enforce HTTPS** in GitHub Pages. Propagation can take time.

Official docs: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site

## Attribution

The layout was closely modeled after https://uhvardhan.github.io/ and its public MIT-licensed repository https://github.com/uhvardhan/uhvardhan.github.io, based on the upstream template https://github.com/leonidk/leonidk.github.io. This is a new implementation with original placeholders, not a copy of the owner's biography or profile images. Review the upstream license and retain any attribution needed if you reuse upstream source verbatim.
