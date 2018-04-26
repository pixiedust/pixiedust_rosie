import classify_data as cd
import pixiedust
from pixiedust.display.app import *
from pixiedust.utils.shellAccess import ShellAccess
from adapt23 import *

@PixieApp
class PixieRosieApp:

    @route()
    def main(self):
        return"""
            <div id=target{{prefix}} class="well">
                <div class="panel panel-primary">
                    <div class="panel-heading">Schema</div>
                    <div class="panel-body">
                        <table class="table table-bordered table-striped">
                            <col width="200">
                            <col width="150">
                            <col width="150">
                            <col width="200">
                            <thead>
                                <th style="text-align: left;">Column Name</th>
                                <th style="text-align: left;">Rosie Type</th>
                                <th style="text-align: left;">Column Type</th>
                                <th style="text-align: left;">Action</th>
                            </thead>
                            {%for display, name, rosie_type, native_type in this.schema.create_schema_table():%}
                                {% if display %}
                                    <tr>
                                        <td style="text-align: left;">{{name}}</td>
                                        <td style="text-align: left;">{{rosie_type}}</td>
                                        <td style="text-align: left;">{{native_type.__name__}}</td>
                                        <td style="text-align: left;">
                                            <button type="submit" pd_options="modify={{loop.index0}}">Rename</button>
                                            <button type="submit" pd_script="self.schema.create_transform({{loop.index0}})" pd_options="transform={{loop.index0}}">Transform</button>
                                            <button type="submit" pd_refresh>Delete
                                                <pd_script type="preRun">
                                                    return confirm("Are you sure you want to delete?");
                                                </pd_script>
                                                <pd_script>
                                                    self.schema.hide_column({{loop.index0}});
                                                </pd_script>
                                            </button>
                                        </td>
                                    </tr>
                                {% endif %}
                            {%endfor%}
                        </table>
                    </div>
                    </div>
                    <br/>
                    <div class="panel panel-primary">
                        <div class="panel-heading">Sample Data</div>
                        <div class="panel-body">
                            <table class="table table-bordered table-striped">
                                <thead>
                                    {%for name in this.schema.colnames:%}
                                        {% if this.schema.column_visibility[loop.index0] %}
                                            <th style="text-align: left;">{{name}}</th>
                                        {% endif %}
                                    {%endfor%}
                                </thead>
                                {%for row in this.schema.sample_data:%}
                                    <tr>
                                    {%for col in row:%}
                                        {% if this.schema.column_visibility[loop.index0] %}
                                            <td style="text-align: left;">{{col}}</td>
                                        {% endif %}
                                    {%endfor%}
                                    </tr>
                                {%endfor%}
                            </table>
                        </div>
                    </div>
                    <input pd_options="RosieUI=true" type="button" value="Finish">
                </div>
            """

    @route(modify="*")
    def modify_screen(self, modify):
        return """
        <div class="well">
            <form>
                <div>
                    <input type="search" id="new_name{{prefix}}" name="colname" placeholder="new name...">
                    <br/>
                    <br/>
                    <input pd_options="home=true" type="button" value="Cancel">
                    <button type="submit" pd_script="self.schema.rename_column({{modify}}, '$val(new_name{{prefix}})')" pd_options="home=true">Rename</button>
                </div>
            </form>
        </div>
        """

    @route(transform="*")
    def transform_screen(self, transform):
        return """
        <div class="well" style="width: 100%; height: 100%; overflow: hidden;">
            <div class="panel panel-primary" style="width: 48%; float: left; margin: 1%;">
                <div class="panel-heading">Rosie Pattern</div>
                <div class="panel-body" style="height: 200px; overflow-y: scroll;">
                    <style>
                        p {
                          text-indent: 4.0em;
                        }
                    </style>
                   {% if this.schema.transform.components == None%}
                        <div class="search">
                             Enter Rosie Pattern: <br/>
                             <input type="text" id="pat{{prefix}}" class="searchTerm">
                             <button type="submit" pd_script="self.schema.set_transform_components('$val(pat{{prefix}})')" pd_options="transform={{transform}}">Extract Variables</button>
                             <button type="submit" pd_options="transform={{transform}}">Use Suggestion
                                <pd_script>
self.schema.suggest_destructuring({{transform}})
                                </pd_script>
                             </button>
                        </div>

                    {% else %}
                        <div class="search">
                             Pattern: <br/>
                             <input type="text" id="pat{{prefix}}" class="searchTerm" value="{{this.schema.toStr(this.schema.transform._pattern._definition)}}" readonly>
                        </div>
                         {%for comp in this.schema.transform.components:%}
                             <p>
                                 <input type="text" class="searchTerm" value="{{this.schema.toStr(comp._name)}}" readonly>
                                 {% if comp._definition%}
                                    <input type="text" id="comp{{loop.index0}}" class="searchTerm" value="{{this.schema.toStr(comp._definition)}}">
                                 {% else %}
                                    <input type="text" id="comp{{loop.index0}}" class="searchTerm" placeholder="Definition">
                                 {% endif %}
                             </p>
                         {%endfor%}
                         <br>
                         <button type="submit" pd_script="self.schema.clear_transform()" pd_options="transform={{transform}}">Clear</button>
                         <button type="submit" pd_options="transform={{transform}}">Create Columns
                            <pd_script>
for idx,comp in enumerate(self.schema.transform.components):
    if (idx == 0):
        comp._definition = bytes23("$val(comp0)")
    elif (idx == 1):
        comp._definition = bytes23("$val(comp1)")
    elif (idx == 2):
        comp._definition = bytes23("$val(comp2)")
    elif (idx == 3):
        comp._definition = bytes23("$val(comp3)")
self.schema.new_columns()
                            </pd_script>
                         </button>

                   {% endif %}
                </div>
            </div>

            <div class="panel panel-primary" style="width: 48%; float: left; margin: 1%;">
                <div class="panel-heading">Rosie Notes</div>
                <div class="panel-body" style="height: 200px; overflow-y: scroll;">
                    <table class="table table-bordered table-striped">
                        {%for row in this.schema.rosie_cheat_sheet:%}
                            <tr>
                            {%for col in row:%}
                                <td style="text-align: left;">{{col}}</td>
                            {%endfor%}
                            </tr>
                        {%endfor%}
                    </table>
                </div>
            </div>
            <br>
            <br>
            <div class="panel panel-primary" style="width: 48%; float: left; margin: 1%;">
                <div class="panel-heading">Selected Column</div>
                <div class="panel-body" style="height: 400px; overflow-y: scroll;">
                    <table class="table table-bordered table-striped">
                        <thead>
                            <th style="text-align: left;">{{this.schema.colnames[transform|int]}}</th>
                        </thead>
                        {%for row in this.schema.sample_data:%}
                            <tr>
                            {%for col in row:%}
                                {% if loop.index0 == transform|int %}
                                    <td style="text-align: left;">{{col}}</td>
                                {% endif %}
                            {%endfor%}
                            </tr>
                        {%endfor%}
                    </table>
                </div>
            </div>

            <div class="panel panel-primary" style="width: 48%; float: left; margin: 1%;">
                <div class="panel-heading">New Column(s)</div>
                <div class="panel-body" style="height: 400px; overflow-y: scroll;">
                    {% if this.schema.transform.errors %}
                        Error Message:
                        {{this.schema.transform.errors}}
                    {% else %}
                        <table class="table table-bordered table-striped">
                            {% if this.schema.transform.new_sample_data %}
                                <thead>
                                    {%for comp in this.schema.transform.components:%}
                                        <th style="text-align: left;">{{this.schema.toStr(comp._name)}}</th>
                                    {%endfor%}
                                </thead>
                                {%for row in this.schema.transform.new_sample_data_display:%}
                                    <tr>
                                    {%for col in row:%}
                                        <td style="text-align: left;">{{col}}</td>
                                    {%endfor%}
                                    </tr>
                                {%endfor%}
                            {% endif %}
                        </table>
                    {% endif %}
                </div>
            </div>
            <input pd_options="home=true" type="button" value="Cancel">
            <button type="submit" pd_script="self.schema.commit_new_columns()" pd_options="home=true"" >Commit Columns</button>
        </div>
        """
