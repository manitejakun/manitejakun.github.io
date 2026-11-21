# Mani Teja portfolio

[maniteja.me](https://maniteja.me) · [Pages CMS](https://app.pagescms.org/) · [Deployment runs](https://github.com/manitejakun/manitejakun.github.io/actions)

## Edit your portfolio

After the first deployment, sign in to Pages CMS with GitHub, open `manitejakun/manitejakun.github.io`, and select **main**. Choose an item in the sidebar, make your changes, then select **Save**. The save creates a GitHub commit and starts the site deployment. Open Deployment runs above and look for a green **Build and deploy portfolio** run, then refresh your site.

| To update | In Pages CMS |
| --- | --- |
| Bio, photo, email or resume | Open **Profile**. Use the photo and PDF pickers to select or upload a file. Add photo alternative text. A selected resume PDF takes priority over the optional external resume link. |
| Social accounts | Open **Social links**. Enter each full URL. For another platform, add a label and URL under **Other social links**. Clear a field to remove its link. |
| College or job | Use **Education** or **Experience → New**. Choose a logo and add dates and a description. An empty end date displays as Present. Both collections use a shared display order. |
| Project | Use **Projects → New**, then add details, a screenshot, and links. Edit an existing entry to update it or use its Delete action to remove it. Featured projects get a discreet label. |
| Award or hackathon | Use **Achievements and hackathons → New**. Add the event, award, date, and a certificate or award image. A visitor can open the image at full size. |
| Publication | Use **Publications → New**. Add the title, authors, venue, year, and available paper links or PDF. |
| Photos | Use **Photos → New** to select or upload an image. Add alternative text, a handwritten caption, and an optional date. Lower display-order values appear first. |
| Article | Use **Writing → New**. Compose in the rich-text editor and add tags, a date, and an optional cover. Leave it on **Draft** while you work. Change to **Published** and save when it is ready. An existing article keeps the address set by its original filename when you edit its title. |

Give earlier timeline entries and projects lower display-order values. For example, assign 10, 20, and 30 so another item can slot in between later. Entries with the same value use their filename as the tie-breaker. Achievements, publications, and articles show the newest first.

For a photo replacement, upload or select the new image in **Profile** and save the form. Use JPG or WebP for photos, PNG for transparent logos, and PDF for your resume. A square photo around 600 pixels and screenshots around 1,200 pixels wide are usually enough. Give screenshots and certificates concise alternative text. Review a PDF or certificate for personal information before uploading it.

This repository is public. Draft articles and uploaded files are visible in GitHub source history even though drafts and unused uploads are omitted from the generated website. Keep private material outside the repository.

## One-time publishing setup

1. Preserve the pre-migration commit on a backup branch before merging the migration. Verify it still matches the previous `main`.
2. In **Settings → Pages → Build and deployment**, select **GitHub Actions** as the source. Check the Custom domain field still contains `maniteja.me`. The repository also retains its `CNAME`.
3. Merge the approved migration to `main`. In **Actions**, confirm that **Build and deploy portfolio** succeeds. If the Pages source was switched after merging, run the workflow manually on `main`.
4. Sign in to Pages CMS and install or authorize its GitHub App for **only** this repository. Open `main` and confirm the nine content groups appear.
5. To test the complete workflow, change and save one genuine profile value in Pages CMS. Verify that Pages CMS created the commit, the Pages deployment succeeded, and the new value appears on `maniteja.me`. Check an uploaded image or PDF the same way. Check the domain over HTTPS and enable **Enforce HTTPS** when GitHub makes it available.

[GitHub Pages publishing documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site) · [Pages CMS setup documentation](https://pagescms.org/docs/quick-start/)

## Source structure

- `.pages.yml` defines the CMS forms and upload folders.
- `content/` holds editable profile, social links, and individual entries.
- `media/images/` and `media/documents/` hold uploads.
- `templates/`, `style.css`, and `images/` hold the design.
- `build.py` renders the site and copies media referenced by published content.
- `.github/workflows/pages.yml` builds pull requests and deploys pushes to `main`.

The static build replaces branch-based publishing. The migration removes the old `.nojekyll` marker because GitHub Actions publishes the generated HTML directly. To preview locally as a maintainer, install `requirements.txt`, run `python build.py`, and serve `_site` with `python -m http.server 8000 --directory _site`. Routine CMS updates require no local build.

The layout preserves the original portfolio’s academic conventions. The original repository README credits [Harshvardhan Uppaluru’s portfolio](https://uhvardhan.github.io/) and [the academic template](https://github.com/leonidk/leonidk.github.io).
