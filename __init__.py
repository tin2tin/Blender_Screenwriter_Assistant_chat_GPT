# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Subtitle Editor",
    "description": "Displays a list of all Subtitle Editor in the VSE and allows editing of their text.",
    "author": "tintwotin",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "Sequencer > Side Bar > Subtitle Editor Tab",
    "warning": "",
    "doc_url": "",
    "support": "COMMUNITY",
    "category": "Sequencer",
}

import os, sys, bpy, pathlib, re
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from datetime import timedelta


def get_strip_by_name(name):
    for strip in bpy.context.scene.sequence_editor.sequences[0:]:
        if strip.name == name:
            return strip
    return None


def find_first_empty_channel(start_frame, end_frame):
    for ch in range(1, len(bpy.context.scene.sequence_editor.sequences_all) + 1):
        for seq in bpy.context.scene.sequence_editor.sequences_all:
            if (
                seq.channel == ch
                and seq.frame_final_start < end_frame
                and seq.frame_final_end > start_frame
            ):
                break
        else:
            return ch
    return 1


def update_text(self, context):
    for strip in bpy.context.scene.sequence_editor.sequences[0:]:
        if strip.type == "TEXT" and strip.name == self.name:
            # Update the text of the text strip
            strip.text = self.text

            break
        strip = get_strip_by_name(self.name)
        if strip:
            # Deselect all strips.
            for seq in context.scene.sequence_editor.sequences_all:
                seq.select = False
            bpy.context.scene.sequence_editor.active_strip = strip
            strip.select = True

            # Set the current frame to the start frame of the active strip
            bpy.context.scene.frame_set(int(strip.frame_start))


# Define a custom property group to hold the text strip name and text
class TextStripItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    text: bpy.props.StringProperty(update=update_text, options={'TEXTEDIT_UPDATE'})
    selected: bpy.props.IntProperty()


class SEQUENCER_UL_List(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        layout.prop(item, "text", text="", emboss=False)


# Define an operator to refresh the list
class SEQUENCER_OT_refresh_list(bpy.types.Operator):
    """Sync items in the list with the text strips"""

    bl_idname = "text.refresh_list"
    bl_label = "Refresh List"

    def execute(self, context):
        active = context.scene.sequence_editor.active_strip
        # Clear the list
        context.scene.text_strip_items.clear()

        # Get a list of all Text Strips in the VSE
        text_strips = [
            strip
            for strip in bpy.context.scene.sequence_editor.sequences
            if strip.type == "TEXT"
        ]

        # Sort the Subtitle Editor based on their start times in the timeline
        text_strips.sort(key=lambda strip: strip.frame_start)

        # Iterate through the sorted text strips and add them to the list
        for strip in text_strips:
            item = context.scene.text_strip_items.add()
            item.name = strip.name
            item.text = strip.text
        # Select only the active strip in the UI list
        for seq in context.scene.sequence_editor.sequences_all:
            seq.select = False
        if active:
            context.scene.sequence_editor.active_strip = active
            active.select = True
            # Set the current frame to the start frame of the active strip
            bpy.context.scene.frame_set(int(active.frame_start))
        return {"FINISHED"}


class SEQUENCER_OT_add_strip(bpy.types.Operator):
    """Add a new text strip after the position of the current selected list item"""

    bl_idname = "text.add_strip"
    bl_label = "Add Text Strip"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        text_strips = scene.sequence_editor.sequences_all

        # Get the selected text strip from the UI list
        index = scene.text_strip_items_index
        items = context.scene.text_strip_items
        un_selected = len(items) - 1 < index
        if not un_selected:
            strip_name = items[index].name
            strip = get_strip_by_name(strip_name)
            cf = context.scene.frame_current
            in_frame = cf + strip.frame_final_duration
            out_frame = cf + (2 * strip.frame_final_duration)
            chan = find_first_empty_channel(in_frame, out_frame)

            # Add a new text strip after the selected strip
            strips = scene.sequence_editor.sequences
            new_strip = strips.new_effect(
                name="Text",
                type="TEXT",
                channel=chan,
                frame_start=in_frame,
                frame_end=out_frame,
            )

            # Copy the settings
            if strip and new_strip:
                new_strip.text = "Text"
                new_strip.font_size = strip.font_size
                new_strip.font = strip.font
                new_strip.color = strip.color
                new_strip.use_shadow = strip.use_shadow
                new_strip.blend_type = strip.blend_type
                new_strip.use_bold = strip.use_bold
                new_strip.use_italic = strip.use_italic
                new_strip.shadow_color = strip.shadow_color
                new_strip.use_box = strip.use_box
                new_strip.box_margin = strip.box_margin
                new_strip.location = strip.location
                new_strip.align_x = strip.align_x
                new_strip.align_y = strip.align_y
                context.scene.sequence_editor.active_strip = new_strip
            self.report({"INFO"}, "Copying settings from the selected item")
        else:
            strips = scene.sequence_editor.sequences
            chan = find_first_empty_channel(
                context.scene.frame_current, context.scene.frame_current + 100
            )

            new_strip = strips.new_effect(
                name="Text",
                type="TEXT",
                channel=chan,
                frame_start=context.scene.frame_current,
                frame_end=context.scene.frame_current + 100,
            )
            new_strip.wrap_width = 0.68
            new_strip.font_size = 44
            new_strip.location[1] = 0.25
            new_strip.align_x = "CENTER"
            new_strip.align_y = "TOP"
            new_strip.use_shadow = True
            new_strip.use_box = True
            context.scene.sequence_editor.active_strip = new_strip
            new_strip.select = True
        # Refresh the UIList
        bpy.ops.text.refresh_list()

        # Select the new item in the UIList
        context.scene.text_strip_items_index = index + 1

        return {"FINISHED"}


class SEQUENCER_OT_delete_strip(bpy.types.Operator):
    """Remove item and strip"""

    bl_idname = "text.delete_strip"
    bl_label = "Remove Item & Strip"

    @classmethod
    def poll(cls, context):
        index = context.scene.text_strip_items_index
        items = context.scene.text_strip_items
        selected = len(items) - 1 < index
        return not selected and context.scene.sequence_editor is not None

    def execute(self, context):
        scene = context.scene
        seq_editor = scene.sequence_editor
        index = context.scene.text_strip_items_index
        items = context.scene.text_strip_items
        if len(items) - 1 < index:
            return {"CANCELLED"}
        # Get the selected text strip from the UI list
        strip_name = items[index].name
        strip = get_strip_by_name(strip_name)
        if strip:
            # Deselect all strips
            for seq in context.scene.sequence_editor.sequences_all:
                seq.select = False
            # Delete the strip
            strip.select = True
            bpy.ops.sequencer.delete()

            # Remove the UI list item
            items.remove(index)
        # Refresh the UIList
        bpy.ops.text.refresh_list()

        return {"FINISHED"}


class SEQUENCER_OT_select_next(bpy.types.Operator):
    """Select the item below"""

    bl_idname = "text.select_next"
    bl_label = "Select Next"

    def execute(self, context):
        scene = context.scene
        current_index = context.scene.text_strip_items_index
        max_index = len(context.scene.text_strip_items) - 1

        if current_index < max_index:
            context.scene.text_strip_items_index += 1
            selected_item = scene.text_strip_items[scene.text_strip_items_index]
            selected_item.select = True
            update_text(selected_item, context)
        return {"FINISHED"}


class SEQUENCER_OT_select_previous(bpy.types.Operator):
    """Select the item above"""

    bl_idname = "text.select_previous"
    bl_label = "Select Previous"

    def execute(self, context):
        scene = context.scene
        current_index = context.scene.text_strip_items_index
        if current_index > 0:
            context.scene.text_strip_items_index -= 1
            selected_item = scene.text_strip_items[scene.text_strip_items_index]
            selected_item.select = True
            update_text(selected_item, context)
        return {"FINISHED"}


class SEQUENCER_OT_insert_newline(bpy.types.Operator):
    bl_idname = "text.insert_newline"
    bl_label = "Insert Newline"
    bl_description = "Inserts a newline character at the cursor position"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        index = context.scene.text_strip_items_index
        items = context.scene.text_strip_items
        selected = len(items) - 1 < index
        return not selected and context.scene.sequence_editor is not None

    def execute(self, context):
        context.scene.text_strip_items[
            context.scene.text_strip_items_index
        ].text += chr(10)
        self.report(
            {"INFO"}, "New line character inserted in the end of the selected item"
        )
        return {"FINISHED"}


def check_pysubs2(self):
    try:
        import pysubs2
    except ModuleNotFoundError:
        import site
        import subprocess
        import sys

        app_path = site.USER_SITE
        if app_path not in sys.path:
            sys.path.append(app_path)
        pybin = sys.executable  # bpy.app.binary_path_python # Use for 2.83

        print("Ensuring: pip")
        try:
            subprocess.call([pybin, "-m", "ensurepip"])
        except ImportError:
            pass
        self.report({"INFO"}, "Installing: pysubs2 module.")
        print("Installing: pysubs2 module")
        subprocess.check_call([pybin, "-m", "pip", "install", "pysubs2"])
        try:
            import pysubs2
        except ModuleNotFoundError:
            print("Installation of the pysubs2 module failed")
            self.report(
                {"INFO"},
                "Installing pysubs2 module failed! Try to run Blender as administrator.",
            )
            return False
    return True


def load_subtitles(file, context, offset):
    if not check_pysubs2(self):
        return {"CANCELLED"}
    render = bpy.context.scene.render
    fps = render.fps / render.fps_base
    fps_conv = fps / 1000

    editor = bpy.context.scene.sequence_editor
    sequences = bpy.context.sequences
    if not sequences:
        addSceneChannel = 1
    else:
        channels = [s.channel for s in sequences]
        channels = sorted(list(set(channels)))
        empty_channel = channels[-1] + 1
        addSceneChannel = empty_channel
    if pathlib.Path(file).is_file():
        if (
            pathlib.Path(file).suffix
            not in pysubs2.formats.FILE_EXTENSION_TO_FORMAT_IDENTIFIER
        ):
            print("Unable to extract subtitles from file")
            self.report({"INFO"}, "Unable to extract subtitles from file")
            return {"CANCELLED"}
    try:
        subs = pysubs2.load(file, fps=fps, encoding="utf-8")
    except:
        print("Import failed. Text encoding must be in UTF-8.")
        self.report({"INFO"}, "Import failed. Text encoding must be in UTF-8.")
        return {"CANCELLED"}
    if not subs:
        print("No file imported.")
        self.report({"INFO"}, "No file imported")
        return {"CANCELLED"}
    for line in subs:
        italics = False
        bold = False
        position = False
        pos = []
        line.text = line.text.replace("\\N", "\n")
        if r"<i>" in line.text or r"{\i1}" in line.text or r"{\i0}" in line.text:
            italics = True
            line.text = line.text.replace("<i>", "")
            line.text = line.text.replace("</i>", "")
            line.text = line.text.replace("{\\i0}", "")
            line.text = line.text.replace("{\\i1}", "")
        if r"<b>" in line.text or r"{\b1}" in line.text or r"{\b0}" in line.text:
            bold = True
            line.text = line.text.replace("<b>", "")
            line.text = line.text.replace("</b>", "")
            line.text = line.text.replace("{\\b0}", "")
            line.text = line.text.replace("{\\b1}", "")
        if r"{" in line.text:
            pos_trim = re.search(r"\{\\pos\((.+?)\)\}", line.text)
            pos_trim = pos_trim.group(1)
            pos = pos_trim.split(",")
            x = int(pos[0]) / render.resolution_x
            y = (render.resolution_y - int(pos[1])) / render.resolution_y
            position = True
            line.text = re.sub(r"{.+?}", "", line.text)
        new_strip = editor.sequences.new_effect(
            name=line.text,
            type="TEXT",
            channel=addSceneChannel,
            frame_start=int(line.start * fps_conv) + offset,
            frame_end=int(line.end * fps_conv) + offset,
        )
        new_strip.text = line.text
        new_strip.wrap_width = 0.68
        new_strip.font_size = 44
        new_strip.location[1] = 0.25
        new_strip.align_x = "CENTER"
        new_strip.align_y = "TOP"
        new_strip.use_shadow = True
        new_strip.use_box = True
        if position:
            new_strip.location[0] = x
            new_strip.location[1] = y
            new_strip.align_x = "LEFT"
        if italics:
            new_strip.use_italic = True
        if bold:
            new_strip.use_bold = True
    # Refresh the UIList
    bpy.ops.text.refresh_list()


def check_overlap(strip1, start, end):
    # Check if the strips overlap.
    # print(str(strip1.frame_final_start + strip1.frame_final_duration)+">="+str(start)+" "+str(strip1.frame_final_start) +" <= "+str(end))
    return (strip1.frame_final_start + strip1.frame_final_duration) >= int(start) and (
        strip1.frame_final_start
    ) <= int(end)


class TEXT_OT_transcribe(bpy.types.Operator):
    bl_idname = "text.transcribe"
    bl_label = "Transcription"
    bl_description = "Transcribe audiofile to text strips"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.sequence_editor

    # Supported languages
    # ['Auto detection', 'Afrikaans', 'Albanian', 'Amharic', 'Arabic', 'Armenian', 'Assamese', 'Azerbaijani', 'Bashkir', 'Basque', 'Belarusian', 'Bengali', 'Bosnian', 'Breton', 'Bulgarian', 'Burmese', 'Castilian', 'Catalan', 'Chinese', 'Croatian', 'Czech', 'Danish', 'Dutch', 'English', 'Estonian', 'Faroese', 'Finnish', 'Flemish', 'French', 'Galician', 'Georgian', 'German', 'Greek', 'Gujarati', 'Haitian', 'Haitian Creole', 'Hausa', 'Hawaiian', 'Hebrew', 'Hindi', 'Hungarian', 'Icelandic', 'Indonesian', 'Italian', 'Japanese', 'Javanese', 'Kannada', 'Kazakh', 'Khmer', 'Korean', 'Lao', 'Latin', 'Latvian', 'Letzeburgesch', 'Lingala', 'Lithuanian', 'Luxembourgish', 'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Maori', 'Marathi', 'Moldavian', 'Moldovan', 'Mongolian', 'Myanmar', 'Nepali', 'Norwegian', 'Nynorsk', 'Occitan', 'Panjabi', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi', 'Pushto', 'Romanian', 'Russian', 'Sanskrit', 'Serbian', 'Shona', 'Sindhi', 'Sinhala', 'Sinhalese', 'Slovak', 'Slovenian', 'Somali', 'Spanish', 'Sundanese', 'Swahili', 'Swedish', 'Tagalog', 'Tajik', 'Tamil', 'Tatar', 'Telugu', 'Thai', 'Tibetan', 'Turkish', 'Turkmen', 'Ukrainian', 'Urdu', 'Uzbek', 'Valencian', 'Vietnamese', 'Welsh', 'Yiddish', 'Yoruba']

    def execute(self, context):
        try:
            import whisper

            # from whisper.utils import write_srt
        except ModuleNotFoundError:
            import site
            import subprocess
            import sys

            app_path = site.USER_SITE
            if app_path not in sys.path:
                sys.path.append(app_path)
            pybin = sys.executable

            try:
                subprocess.call([pybin, "-m", "ensurepip"])
            except ImportError:
                pass
            self.report({"INFO"}, "Installing: Whisper module.")
            print("Installing: Whisper module")
            subprocess.check_call(
                [
                    pybin,
                    "-m",
                    "pip",
                    "install",
                    "git+https://github.com/openai/whisper.git",
                    "--user",
                ]
            )
            try:
                import whisper

                # from whisper.utils import write_srt
                # self.report({"INFO"}, "Detected: Whisper module.")
                # print("Detected: Whisper module")
            except ModuleNotFoundError:
                print("Installation of the Whisper module failed")
                self.report(
                    {"INFO"},
                    "Installing Whisper module failed! Try to run Blender as administrator.",
                )
                return {"CANCELLED"}
        current_scene = bpy.context.scene
        try:
            active = current_scene.sequence_editor.active_strip
        except AttributeError:
            self.report({"INFO"}, "No active strip selected!")
            return {"CANCELLED"}
        if not active:
            self.report({"INFO"}, "No active strip!")
            return {"CANCELLED"}
        if not active.type == "SOUND":
            self.report({"INFO"}, "Active strip is not a sound strip!")
            return {"CANCELLED"}
        offset = int(active.frame_start)
        clip_start = int(active.frame_start + active.frame_offset_start)
        clip_end = int(
            active.frame_start + active.frame_final_duration
        )  # -active.frame_offset_end)

        sound_path = bpy.path.abspath(active.sound.filepath)
        output_dir = os.path.dirname(sound_path)
        audio_basename = os.path.basename(sound_path)

        model = whisper.load_model("tiny")  # or whatever model you prefer
        result = model.transcribe(sound_path)

        transcribe = model.transcribe(sound_path)
        segments = transcribe["segments"]

        out_dir = os.path.join(output_dir, audio_basename + ".srt")
        if os.path.exists(out_dir):
            os.remove(out_dir)
        segmentId = 0
        for segment in segments:
            startTime = str(0) + str(timedelta(seconds=int(segment["start"]))) + ",000"
            endTime = str(0) + str(timedelta(seconds=int(segment["end"]))) + ",000"
            text = segment["text"]
            segmentId = segment["id"] + 1
            segment = f"{segmentId}\n{startTime} --> {endTime}\n{text[1:] if text[0] == ' ' else text}\n\n"
            # srtFilename = out_dir + audio_basename + ".srt"
            with open(out_dir, "a", encoding="utf-8") as srtFile:
                srtFile.write(segment)
        # save SRT
        #        with open(out_dir, "w", encoding="utf-8") as srt:
        #            write_srt(result["segments"], file=srt)
        # offset = 0
        if os.path.exists(out_dir):
            load_subtitles(out_dir, context, offset)
        return {"FINISHED"}


class SEQUENCER_OT_import_subtitles(Operator, ImportHelper):
    """Import Subtitles"""

    bl_idname = "sequencer.import_subtitles"
    bl_label = "Import"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = [".srt", ".ass"]

    filter_glob: StringProperty(
        default="*.srt;*.ass;*.ssa;*.mpl2;*.tmp;*.vtt;*.microdvd",
        options={"HIDDEN"},
        maxlen=255,
    )

    do_translate: BoolProperty(
        name="Translate Subtitles",
        description="Translate subtitles",
        default=False,
        options={"HIDDEN"},
    )

    translate_from: EnumProperty(
        name="From",
        description="Translate from",
        items=(
            ("auto", "Any language (detect)", ""),
            ("bg", "Bulgarian", ""),
            ("zh", "Chinese", ""),
            ("cs", "Czech", ""),
            ("da", "Danish", ""),
            ("nl", "Dutch", ""),
            ("en", "English", ""),  # Only usable for source language
            # ("en-US", "English (American)", ""),  # Only usable for destination language
            # ("en-GB", "English (British)", ""),  # Only usable for destination language
            ("et", "Estonian", ""),
            ("fi", "Finnish", ""),
            ("fr", "French", ""),
            ("de", "German", ""),
            ("el", "Greek", ""),
            ("hu", "Hungarian", ""),
            ("id", "Indonesian", ""),
            ("it", "Italian", ""),
            ("ja", "Japanese", ""),
            ("lv", "Latvian", ""),
            ("lt", "Lithuanian", ""),
            ("pl", "Polish", ""),
            ("pt", "Portuguese", ""),  # Only usable for source language
            # ("pt-PT", "Portuguese", ""),  # Only usable for destination language
            # ("pt-BR", "Portuguese (Brazilian)", ""),  # Only usable for destination language
            ("ro", "Romanian", ""),
            ("ru", "Russian", ""),
            ("sk", "Slovak", ""),
            ("sl", "Slovenian", ""),
            ("es", "Spanish", ""),
            ("sv", "Swedish", ""),
            ("tr", "Turkish", ""),
            ("uk", "Ukrainian", ""),
        ),
        default="auto",
        options={"HIDDEN"},
    )

    translate_to: EnumProperty(
        name="To",
        description="Translate to",
        items=(
            # ("auto", "Any language (detect)", ""),
            ("bg", "Bulgarian", ""),
            ("zh", "Chinese", ""),
            ("cs", "Czech", ""),
            ("da", "Danish", ""),
            ("nl", "Dutch", ""),
            # ("en", "English", ""),  # Only usable for source language
            ("en-US", "English (American)", ""),  # Only usable for destination language
            ("en-GB", "English (British)", ""),  # Only usable for destination language
            ("et", "Estonian", ""),
            ("fi", "Finnish", ""),
            ("fr", "French", ""),
            ("de", "German", ""),
            ("el", "Greek", ""),
            ("hu", "Hungarian", ""),
            ("id", "Indonesian", ""),
            ("it", "Italian", ""),
            ("ja", "Japanese", ""),
            ("lv", "Latvian", ""),
            ("lt", "Lithuanian", ""),
            ("pl", "Polish", ""),
            # ("pt", "Portuguese", ""),  # Only usable for source language
            ("pt-PT", "Portuguese", ""),  # Only usable for destination language
            (
                "pt-BR",
                "Portuguese (Brazilian)",
                "",
            ),  # Only usable for destination language
            ("ro", "Romanian", ""),
            ("ru", "Russian", ""),
            ("sk", "Slovak", ""),
            ("sl", "Slovenian", ""),
            ("es", "Spanish", ""),
            ("sv", "Swedish", ""),
            ("tr", "Turkish", ""),
            ("uk", "Ukrainian", ""),
        ),
        default="en-US",
        options={"HIDDEN"},
    )

    def execute(self, context):
        if self.do_translate:
            try:
                from srtranslator import SrtFile
                from srtranslator.translators.deepl import DeeplTranslator
            except ModuleNotFoundError:
                import site
                import subprocess
                import sys

                app_path = site.USER_SITE
                if app_path not in sys.path:
                    sys.path.append(app_path)
                pybin = sys.executable  # bpy.app.binary_path_python # Use for 2.83

                print("Ensuring: pip")
                try:
                    subprocess.call([pybin, "-m", "ensurepip"])
                except ImportError:
                    pass
                self.report({"INFO"}, "Installing: srtranslator module.")
                print("Installing: srtranslator module")
                subprocess.check_call([pybin, "-m", "pip", "install", "srtranslator"])
                try:
                    from srtranslator import SrtFile
                    from srtranslator.translators.deepl import DeeplTranslator

                    self.report({"INFO"}, "Detected: srtranslator module.")
                    print("Detected: srtranslator module")
                except ModuleNotFoundError:
                    print("Installation of the srtranslator module failed")
                    self.report(
                        {"INFO"},
                        "Installing srtranslator module failed! Try to run Blender as administrator.",
                    )
                    return {"CANCELLED"}
            file = self.filepath
            if not file:
                return {"CANCELLED"}
                print("Invalid file")
                self.report({"INFO"}, "Invalid file")
            translator = DeeplTranslator()
            if pathlib.Path(file).is_file():
                print("Translating. Please Wait.")
                self.report({"INFO"}, "Translating. Please Wait.")
                srt = SrtFile(file)
                srt.translate(translator, self.translate_from, self.translate_to)

                # Making the result subtitles prettier
                srt.wrap_lines()

                srt.save(f"{os.path.splitext(file)[0]}_translated.srt")
                translator.quit()
                print("Translating finished.")
                self.report({"INFO"}, "Translating finished.")
        file = self.filepath
        if self.do_translate:
            file = f"{os.path.splitext(file)[0]}_translated.srt"
        if not file:
            return {"CANCELLED"}
        offset = 0
        load_subtitles(file, context, offset)

        return {"FINISHED"}

    def draw(self, context):
        pass


class SEQUENCER_PT_import_subtitles(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Translation"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SEQUENCER_OT_import_subtitles"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator
        layout = layout.column(heading="Translate Subtitles")
        layout.prop(operator, "do_translate", text="")
        col = layout.column(align=False)
        col.prop(operator, "translate_from", text="From")
        col.prop(operator, "translate_to", text="To")
        col.active = operator.do_translate


def frame_to_ms(frame):
    """Converts a frame number to a time in milliseconds, taking the frame rate of the scene into account."""
    scene = bpy.context.scene
    fps = (
        scene.render.fps / scene.render.fps_base
    )  # Calculate the frame rate as frames per second.
    ms_per_frame = 1000 / fps  # Calculate the number of milliseconds per frame.
    return frame * ms_per_frame


class SEQUENCER_OT_export_list_subtitles(Operator, ImportHelper):
    """Export Subtitles"""

    bl_idname = "sequencer.export_list_subtitles"
    bl_label = "Export"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = [".srt", ".ass"]

    filter_glob: StringProperty(
        default="*.srt;*.ass;*.ssa;*.mpl2;*.tmp;*.vtt;*.microdvd;*.fountain",
        options={"HIDDEN"},
        maxlen=255,
    )

    formats: EnumProperty(
        name="Formats",
        description="Format to save as",
        items=(
            ("srt", "srt", "SubRip"),
            ("ass", "ass", "SubStationAlpha"),
            ("ssa", "ssa", "SubStationAlpha"),
            ("mpl2", "mpl2", "MPL2"),
            # ("tmp", "tmp", "TMP"),
            ("vtt", "vtt", "WebVTT"),
            #("microdvd", "microdvd", "MicroDVD"),
            ("fountain", "fountain", "Fountain Screenplay"),
        ),
        default="srt",
    )

    def execute(self, context):
        if not check_pysubs2(self):
            return {"CANCELLED"}
        # Get a list of all Text Strips in the VSE
        text_strips = [
            strip
            for strip in bpy.context.scene.sequence_editor.sequences
            if strip.type == "TEXT"
        ]

        # Sort the Subtitle Editor based on their start times in the timeline
        text_strips.sort(key=lambda strip: strip.frame_start)

        from pysubs2 import SSAFile, SSAEvent, make_time

        file_name = self.filepath
        if pathlib.Path(file_name).suffix != "." + self.formats:
            file_name = self.filepath + "." + self.formats
        if self.formats != "fountain":
            subs = SSAFile()
            # Iterate through the sorted text strips and add them to the list
            for strip in text_strips:
                event = SSAEvent()
                event.start = frame_to_ms(strip.frame_final_start)
                event.end = frame_to_ms(
                    strip.frame_final_start + strip.frame_final_duration
                )
                event.text = strip.text
                event.bold = strip.use_bold
                event.italic = strip.use_italic
                
                subs.append(event)
            text = subs.to_string(self.formats)
#            if self.formats == "microdvd": #doesn't work
#                subs.save(file_name, format_="microdvd", fps=(scene.render.fps / scene.render.fps_base))
            if self.formats == "mpl2":
                subs.save(file_name, format_="mpl2")
            else:
                subs.save(file_name)
        else:
            text = ""
            # Iterate through the sorted text strips and add them to the list
            for strip in text_strips:
                text = text + strip.text + chr(10) + chr(13) + " " + chr(10) + chr(13)
            fountain_file = open(file_name, "w")
            fountain_file.write(text)
            fountain_file.close()
        return {"FINISHED"}

    def draw(self, context):
        pass


class SEQUENCER_PT_export_list_subtitles(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "File Formats"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SEQUENCER_OT_export_list_subtitles"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator
        layout = layout.column(heading="File Formats")
        layout.prop(operator, "formats", text="Format")


class SEQUENCER_OT_copy_textprops_to_selected(Operator):
    """Copy properties from active text strip to selected text strips"""

    bl_idname = "sequencer.copy_textprops_to_selected"
    bl_label = "Copy Properties to Selected"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        current_scene = bpy.context.scene
        try:
            active = current_scene.sequence_editor.active_strip
        except AttributeError:
            self.report({"INFO"}, "No active strip selected")
            return {"CANCELLED"}
        for strip in context.selected_sequences:
            if strip.type == active.type == "TEXT":
                strip.wrap_width = active.wrap_width
                strip.font = active.font
                strip.use_italic = active.use_italic
                strip.use_bold = active.use_bold
                strip.font_size = active.font_size
                strip.color = active.color
                strip.use_shadow = active.use_shadow
                strip.shadow_color = active.shadow_color
                strip.use_box = active.use_box
                strip.box_color = active.box_color
                strip.box_margin = active.box_margin
                strip.location[0] = active.location[0]
                strip.location[1] = active.location[1]
                strip.align_x = active.align_x
                strip.align_y = active.align_y
        return {"FINISHED"}


# Define the panel to hold the UIList and the refresh button
class SEQUENCER_PT_panel(bpy.types.Panel):
    bl_idname = "SEQUENCER_PT_panel"
    bl_label = "Subtitle Editor"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Subtitle Editor"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.template_list(
            "SEQUENCER_UL_List",
            "",
            context.scene,
            "text_strip_items",
            context.scene,
            "text_strip_items_index",
            rows=14,
        )

        row = row.column(align=True)
        row.operator("text.refresh_list", text="", icon="FILE_REFRESH")

        row.separator()

        row.operator("sequencer.import_subtitles", text="", icon="IMPORT")
        row.operator("sequencer.export_list_subtitles", text="", icon="EXPORT")

        row.separator()

        row.operator("text.add_strip", text="", icon="ADD", emboss=True)
        row.operator("text.delete_strip", text="", icon="REMOVE", emboss=True)

        row.separator()

        row.operator("text.select_previous", text="", icon="TRIA_UP")
        row.operator("text.select_next", text="", icon="TRIA_DOWN")

        row.separator()

        row.operator("text.insert_newline", text="", icon="EVENT_RETURN")


def import_subtitles(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("sequencer.import_subtitles", text="Subtitles", icon="ALIGN_BOTTOM")


def transcribe(self, context):
    layout = self.layout
    layout.separator()
    layout.operator("text.transcribe", text="Transcriptions", icon="SPEAKER")


def copyto_panel_append(self, context):
    strip = context.active_sequence_strip
    strip_type = strip.type
    if strip_type == "TEXT":
        layout = self.layout
        layout.operator(SEQUENCER_OT_copy_textprops_to_selected.bl_idname)


def setText(self, context):
    scene = context.scene
    current_index = context.scene.text_strip_items_index
    max_index = len(context.scene.text_strip_items) - 1

    if current_index < max_index:
        selected_item = scene.text_strip_items[scene.text_strip_items_index]
        selected_item.select = True
        update_text(selected_item, context)


classes = (
    TextStripItem,
    SEQUENCER_UL_List,
    SEQUENCER_OT_refresh_list,
    SEQUENCER_OT_add_strip,
    SEQUENCER_OT_delete_strip,
    SEQUENCER_OT_select_next,
    SEQUENCER_OT_select_previous,
    SEQUENCER_OT_insert_newline,
    SEQUENCER_OT_import_subtitles,
    SEQUENCER_PT_import_subtitles,
    SEQUENCER_OT_export_list_subtitles,
    SEQUENCER_PT_export_list_subtitles,
    SEQUENCER_OT_copy_textprops_to_selected,
    TEXT_OT_transcribe,
    SEQUENCER_PT_panel,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.text_strip_items = bpy.props.CollectionProperty(type=TextStripItem)
    bpy.types.Scene.text_strip_items_index = bpy.props.IntProperty(
        name="Index for Subtitle Editor", default=0, update=setText
    )
    bpy.types.SEQUENCER_MT_add.append(import_subtitles)
    bpy.types.SEQUENCER_MT_add.append(transcribe)
    bpy.types.SEQUENCER_PT_effect.append(copyto_panel_append)


def unregister():
    bpy.types.SEQUENCER_PT_effect.remove(copyto_panel_append)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.text_strip_items
    del bpy.types.Scene.text_strip_items_index
    bpy.types.SEQUENCER_MT_add.remove(import_subtitles)
    bpy.types.SEQUENCER_MT_add.append(transcribe)


# Register the addon when this script is run
if __name__ == "__main__":
    register()
