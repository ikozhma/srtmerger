# srtmerger
![s](https://cloud.githubusercontent.com/assets/1775045/11559585/608ac4fa-99cf-11e5-91a2-3ea93ae98a3a.png)
subtitle merger is a tool for merging two or more subtitles for videos.
SRT Merger allows you to merge subtitle files, no matter what language are the subtitles encoded in. The result of this merge will be a new subtitle file which will display subtitles from each merged file.

## How to works?
    m = Merger(output_name="new.srt")
    m.add('fa.srt', color="yellow", codec="windows-1256")
    m.add('en.srt')
    m.merge()


# How to install cli-script if you have `uv`:

1) Clone the repo 

2) From repo folder execute this command

```bash
uv tool install .
```

3) After that you can use scipt

```bash
merge-subs --help
```