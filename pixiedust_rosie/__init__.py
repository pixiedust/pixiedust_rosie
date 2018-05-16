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
from pixiedust.utils.sampleData import Downloader, SampleData, dataDefs
from .pixie_rosie_UI_FACTORED import PixieRosieApp

def wrangle_data(url=None):
    """
    Main public API that performs the following operations:
    1. Download the url in a local directory
    2. Call the PixieRosieApp UI
    3. Create a Pandas DataFrame with the user selections
    """

    if url is None:
        return SampleData(dataDefs, False).printSampleDataList()

    def data_loader(path, schema):
        """Invoke the PixieRosieApp with the path to the local file"""
        PixieRosieApp().run(path)

    if str(url) in dataDefs:
        url = dataDefs[str(url)]['url']

    Downloader({
            "displayName": url,
            "url": url
}, True).download( data_loader )
