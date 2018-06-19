# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2018
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------

import pixiedust_rosie.classify.classify_data as cd
import pixiedust
from pixiedust.display.app import *
from pixiedust.utils.shellAccess import ShellAccess

@PixieApp
class PixieRosieApp:

    def setup(self):
        self.schema = cd.Schema(self.pixieapp_entity, 50)
        self.schema.load_and_process()

    @route()
    def main(self):
        return self.env.getTemplate("schema_screen.html")

    @route(modify_state="*")
    def modify_screen(self, modify_state):
        return self.env.getTemplate("modify_screen.html")

    @route(transform_state="*")
    def transform_screen(self, transform_state):
        return self.env.getTemplate("transform_screen.html")

    @route(suggestion_state="*")
    def suggestion_screen(self, suggestion_state):
        return self.env.getTemplate("suggestion_screen.html")

    @route(finish_state="*")
    def finish_screen(self, finish_state):
        return self.env.getTemplate("finish_screen.html")

    @route(pattern_state="*")
    def pattern_panel(self, pattern_state):
        return self.env.getTemplate("pattern_panel.html")

    @route(help_state="*")
    def help_panel(self, help_state):
        return self.env.getTemplate("help_panel.html")

    @route(newColumns_state="*")
    def newColumns_panel(self, newColumns_state):
        return self.env.getTemplate("newColumns_panel.html")

    @route(tranButtons_state="*")
    def transform_buttons(self, tranButtons_state):
        return self.env.getTemplate("transform_buttons.html")
