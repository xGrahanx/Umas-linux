
# Assets Migration Guide

If you've cloned my repo before I moved all assets to [releases tag](https://github.com/iluvgirlswithglasses/linux-desktop-gremlin/releases), you might want to do this to avoid re-downloading assets after `git pull`:

```sh
cd ~/.config/linux-desktop-gremlin/     # move to project directory
git pull                                # update source code
git checkout 0568a6b                    # go back to the commit where all assets are still there
mv gremlins _gremlins                   # store the assets somewhere else
git switch -                            # switch back to the newest commit
mv _gremlins gremlins                   # put the assets back where they belong
./scripts/make-desktop-files.sh         # create desktop files, including the new GUI for downloading assets
```

**Note:** The steps above only restore assets up to commit 0568a6b. They do not include:
- New gremlins added afterward
- Updated versions of existing assets

To get the latest assets and future updates, please visit the [releases tag](https://github.com/iluvgirlswithglasses/linux-desktop-gremlin/releases) and download them from there using the [new downloader](./03-download-gremlin-assets.md).
