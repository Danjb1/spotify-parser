import json
import os
import sys

from dataclasses import dataclass
from io import StringIO

@dataclass
class Track:
    name: str
    artist: str
    album: str


@dataclass
class Playlist:
    name: str
    tracks: list[Track]


class PlaylistParser:
    def __init__(self, json_filename: str, data: dict[str, Any]):
        self.errors = []
        self.json_filename = json_filename
        self.playlists = self.__parse_playlists(data)


    def __parse_playlists(self, data: dict[str, Any]) -> list[Playlist]:
        if "playlists" not in data:
            self.errors.append("Failed to find 'playlists' in JSON")
            return []

        playlists_json = data["playlists"]

        if not isinstance(playlists_json, list):
            self.errors.append("'playlists' is not a list")
            return []

        playlists = []

        for playlist_json in playlists_json:
            playlist = self.__parse_playlist(playlist_json)
            if playlist is not None:
                playlists.append(playlist)

        return playlists


    def __parse_playlist(self, data: dict[str, Any]) -> Playlist | None:
        if "name" not in data:
            self.errors.append("Failed to find 'name' in playlist")
            return None

        name = data["name"]

        if "items" not in data:
            self.errors.append(f"Failed to find 'items' in playlist: {name}")
            return None

        items_json = data["items"]

        if not isinstance(items_json, list):
            self.errors.append(f"'items' is not a list in playlist: {name}")
            return None

        tracks = []

        for item_json in items_json:
            track = self.__parse_track(item_json)
            if track is not None:
                tracks.append(track)

        return Playlist(name, tracks)


    def __parse_track(self, data: dict[str, Any]) -> Track | None:
        if "track" not in data:
            self.errors.append("Failed to find 'track' in playlist item")
            return None

        track_json = data["track"]
        if track_json is None:
            # Item could be an episode, audiobook or localTrack.
            # For now we only support localTracks; episodes and audiobooks will be skipped.
            return self.__parse_local_track(data)

        try:
            return Track(
                track_json["trackName"],
                track_json["artistName"],
                track_json["albumName"],
            )
        except KeyError as e:
            self.errors.append(f"Missing key for track: {e}")
            return None


    def __parse_local_track(self, data: dict[str, Any]) -> Track | None:
        # User-uploaded tracks look like this:
        #   {
        #     "localTrack": {
        #       "uri": "spotify:local:[Artist]:[Album]:[TrackName]:[Duration]"
        #     }
        #   }
        if "localTrack" not in data:
            return None

        local_track_json = data["localTrack"]
        if local_track_json is None:
            return None

        if "uri" not in local_track_json:
            self.errors.append("localTrack has no uri")
            return None

        uri = local_track_json["uri"]
        uri_parts = uri.split(":")

        artist = uri_parts[2]
        album = uri_parts[3]
        name = uri_parts[4]

        return Track(name, artist, album)


    def save_results(self, output_dir: str) -> None:
        output_filename = f"{output_dir}/index.html"
        with open(output_filename, "w", encoding="utf-8") as file:
            file.write(self.__get_html_content())


    def __get_html_content(self) -> str:
        return f"""<!DOCTYPE html>
<html>
    <head>
        <title>Spotify Playlists</title>
        <style>{self.__get_stylesheet()}</style>
    </head>
    <body>
        <h1>{self.json_filename}</h2>

        {self.__get_errors_html()}

        <section>
            <h2>Playlists</h2>
            {self.__get_playlists_html()}
        </section>
    </body>
</html>"""


    def __get_stylesheet(self) -> str:
        return """th {
  text-align: left;
}"""


    def __get_errors_html(self) -> str:
        if len(self.errors) == 0:
            return ""

        error_str = f"""<ul>
    <li>
    {"</li>\n<li>".join(self.errors)}
    </li>
</ul>"""

        return f"""<section>
    <h2>Errors</h2>
    {error_str}
</section>"""


    def __get_playlists_html(self) -> str:
        if len(self.playlists) == 0:
            return "<p>No playlists found!</p>"

        playlist_rows_io = StringIO()

        # Write contents
        playlist_rows_io.write(self.__get_contents_html())

        # Write playlists
        for playlist in self.playlists:
            playlist_html = self.__get_playlist_html(playlist)
            playlist_rows_io.write(playlist_html)

        return playlist_rows_io.getvalue()


    def __get_contents_html(self) -> str:
        if len(self.playlists) == 0:
            return ""

        contents_io = StringIO()
        for playlist in self.playlists:
            contents_io.write(f'<li><a href="#{playlist.name}">{playlist.name}</a></li>')

        return f"""<ul>
    {contents_io.getvalue()}
</ul>"""


    def __get_playlist_html(self, playlist: Playlist) -> str:
        playlist_rows_io = StringIO()

        for track in playlist.tracks:
            playlist_rows_io.write(f"""<tr>
    <td>{track.name}</td>
    <td>{track.artist}</td>
    <td>{track.album}</td>
</tr>""")

        return f"""
    <h3><a id="{playlist.name}">{playlist.name}</a></h3>
    <table>
        <tr>
            <th>Track Name</th>
            <th>Artist</th>
            <th>Album</th>
        </tr>
        {playlist_rows_io.getvalue()}
    </table>
</section>"""


def main():
    # Parse arguments
    if len(sys.argv) < 2:
        print("Expected:\npython parser.py path/to/Playlist1.json [output_dir]")
        return

    filename = sys.argv[1]

    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = "output"

    # Create the output directory
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except PermissionError:
            print(f"Could not create output directory due to permission error: {output_dir}")
        except Exception as e:
            print(f"Error creating output directory: {e}")

    # Parse JSON
    print(f"Parsing: {filename}")

    data = {}
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"File not found: {filename}")
    except PermissionError:
        print(f"Could not read file: {filename}")
    except json.JSONDecodeError as e:
        print(f"Could not parse JSON: {e.msg}")
    except Exception as e:
        print(f"Error reading playlists: {e}")

    if not data:
        return

    # Parse playlists from JSON data
    parser = PlaylistParser(filename, data)
    print(f"Parse completed with {len(parser.errors)} errors and {len(parser.playlists)} playlists")

    # Save results
    print(f"Saving results to: {output_dir}")
    try:
        parser.save_results(output_dir)
        print("Success!")
    except Exception as e:
        print(f"Error saving results: {e}")


if __name__ == "__main__":
    main()
