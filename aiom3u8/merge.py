import os
import re
import subprocess

from printy import printy

from .params_def import (
    CONCAT_FILE_CONTAINER,
    CONCAT_FILE_TXT,
    CONCAT_FILE_BAT,
    CONCAT_OBJECT_NAME,
    FILE_SC
)


format_rules = {
    "EXT-X-MAP": re.compile(r'#EXT-X-MAP:URI="(.*?)"(?:,BYTERANGE="(.*)")?')
}


class Merge:
    __slots__ = (
        "_m3u8_content",
        "_init_mp4_required",
        "_init_mp4_uri",
        "_init_mp4_byterange",
        "_video_path",
        "_video_name",
        "_slices_path",
        "_extra_clean_up_storage",
        "is_slices_replace",
        "slices_replace_reflection"
    )

    def __init__(
        self,
        m3u8_content: str,
        video_path: str,
        video_name: str,
        slices: list
    ) -> None:
        self._init_mp4_required = False
        self._video_path = video_path
        self._video_name = video_name
        self._extra_clean_up_storage = []

        # figuring out the specific merging way
        res = format_rules["EXT-X-MAP"].findall(m3u8_content)

        if res:
            self._init_mp4_required = True
            self._init_mp4_uri = res[0][0]
            self._init_mp4_byterange = res[1][0] if len(res) == 2 else None

            slices.insert(0, res[0][0])

        # handle case that slice name contain the char cant be writen as file name
        self.is_slices_replace = False
        for slice_ in slices:
            _ = slice_[slice_.rfind('/') + 1:] if slice_.startswith("http") or slice_[0] == '/' else slice_
            if any([_.find(ch) != -1 for ch in FILE_SC]):
                self.is_slices_replace = True

            if self.is_slices_replace:
                break

        if self.is_slices_replace:
            self.slices_replace_reflection = {}
            self._slices_path = []

            for index, slice_ in enumerate(slices):
                new_file_name = str(index) + (".ts" if slice_.endswith(".ts") else '')
                self.slices_replace_reflection.update(
                    {slice_: new_file_name}
                )
                self._slices_path.append(os.path.join(self._video_path, new_file_name))
        else:
            self._slices_path = [os.path.join(self._video_path, slice_[slice_.rfind('/') + 1:]) for slice_ in slices]

    @property
    def pre_uri(self):
        """ init video need to be fetched before merging """

        if self._init_mp4_required:
            return self._init_mp4_uri
        else:
            return None

    def start(self):
        printy("Merging... (It may take for a while)", flags="r>")

        if self._init_mp4_required:
            self._process_type_x_map()
        else:
            self._process_type_default()

        self._clean_up_residues()

        printy("DONE", flags="r>")

    def _process_type_x_map(self) -> None:
        """
        merge slices in `EXT-X-MAP` way
        1. Combine all the M4S files that comprise a single streamed video into one M4S file.
        2. Convert the combined M4S file into an .MP4 file.
        """

        # make sure the init video has been downloaded
        init_video_exist = False

        for _ in os.listdir(self._video_path):
            if _.find(".mp4") != -1:
                init_video_exist = True
                break

        if not init_video_exist:
            raise Exception("can not merge slices without init video")

        # build up .bat file to create concatenated file
        concat_file_txt_path = os.path.join(self._video_path, CONCAT_FILE_TXT)
        concat_file_bat_path = os.path.join(self._video_path, CONCAT_FILE_BAT)
        mid_object_path = os.path.join(self._video_path, CONCAT_OBJECT_NAME)
        final_video_path = os.path.join(self._video_path, self._video_name)

        with open(concat_file_txt_path, 'w') as concat_bat_file:
            for index, slice_path in enumerate(self._slices_path):
                if not index:
                    concat_bat_file.write(f'type "{slice_path}" >"{mid_object_path}"\n')
                else:
                    concat_bat_file.write(f'type "{slice_path}" >>"{mid_object_path}"\n')

            concat_bat_file.write("exit")

        os.rename(concat_file_txt_path, concat_file_bat_path)
        proc = subprocess.Popen(
            concat_file_bat_path,
            cwd=self._video_path,
            stdout=subprocess.PIPE
        )
        proc.communicate()

        # convert concatenated file to final video that can be viewed
        proc = subprocess.Popen(
            f"ffmpeg.exe -y -i {mid_object_path} -c copy {final_video_path}",
            cwd=os.path.abspath(os.path.dirname(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        proc.communicate()

    def _process_type_default(self) -> None:
        """
        merge slices in default way
        Combine all the slices with ffmpeg concat instruction
        """
        _tgt_slices_path = [slice_path + ".ts" if not slice_path.endswith(".ts") else slice_path
                            for slice_path in self._slices_path]

        cwd_ = os.path.abspath(os.path.dirname(__file__))

        for index, _path in enumerate(_tgt_slices_path):
            _slice_path = self._slices_path[index]

            if not _slice_path.endswith(".ts"):
                subprocess.Popen(
                    f"ffmpeg.exe -y -f mpegts -i {_slice_path} -c copy {_path}",
                    cwd=cwd_,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True
                ).communicate()

        self._extra_clean_up_storage += _tgt_slices_path

        concat_file_container_path = os.path.join(self._video_path, CONCAT_FILE_CONTAINER)
        final_video_path = os.path.join(self._video_path, self._video_name)

        with open(concat_file_container_path, 'w') as concat_bat_file:
            for index, slice_path in enumerate(_tgt_slices_path):
                concat_bat_file.write(f"file '{slice_path}'\n")

        proc = subprocess.Popen(
            f"ffmpeg.exe -y -safe 0 -f concat -i {concat_file_container_path} -c copy {final_video_path}",
            cwd=cwd_,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True
        )
        proc.communicate()

    def _clean_up_residues(self) -> None:
        for _ in self._slices_path + self._extra_clean_up_storage:
            if os.path.isfile(_):
                os.remove(_)

        if self._init_mp4_required:
            # remove .bat file and concatenated file
            concat_file_bat_path = os.path.join(self._video_path, CONCAT_FILE_BAT)
            mid_object_path = os.path.join(self._video_path, CONCAT_OBJECT_NAME)

            if os.path.isfile(concat_file_bat_path):
                os.remove(concat_file_bat_path)

            if os.path.isfile(mid_object_path):
                os.remove(mid_object_path)
        else:
            # remove .txt file
            concat_file_container_path = os.path.join(self._video_path, CONCAT_FILE_CONTAINER)

            if os.path.isfile(concat_file_container_path):
                os.remove(concat_file_container_path)
