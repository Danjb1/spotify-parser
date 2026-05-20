# Spotify Parser

A Python script to parse downloaded playlist data from Spotify into a user-readable HTML page.

## Background

Spotify allows you to [request a copy](https://www.spotify.com/account/privacy/) of all your data. This includes a `Playlist1.json` file containing all of your playlists, in the form:

```
{
  "playlists": [
    {
      "name": "Best Playlist Ever",
      "items": [
        {
          "track": {
            "trackName": "Never Gonna Give You Up",
            "artistName": "Rick Astley",
            "albumName": "Whenever You Need Somebody "
        },
        ...
      ],
    },
    ...
  ]
}
```

I wanted a way to read my playlists more easily so I wrote a parser for this file that outputs the playlists as HTML.

## Usage

```
python parser.py path/to/Playlist1.json [output_dir]
```

The `output_dir` argument is optional, and will default to `output`.
