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
        <link rel="stylesheet" href="/Users/tantony/Downloads/fontawesome-free-5.0.10/web-fonts-with-css/css/fontawesome.min.css">
            <div id=target{{prefix}} class="well">
                <H1 style="text-align: center;font-size: 180%;">Wrangle Data: Schema</H1>
                <br>
                <div class="panel panel-primary">
                    <div class="panel-heading">Schema</div>
                    <div class="panel-body">
                        <table class="table table-bordered table-striped">
                            <col width="150">
                            <col width="150">
                            <col width="150">
                            <col width="90">
                            <thead>
                                <th style="text-align: left;">Column Name</th>
                                <th style="text-align: left;">Rosie Type</th>
                                <th style="text-align: left;">Column Type</th>
                                <th style="text-align: left;">Actions</th>
                            </thead>
                            {%for display, name, rosie_type, native_type in this.schema.create_schema_table():%}
                                {% if display %}
                                    <tr>
                                        <td style="text-align: left;">{{name}}</td>
                                        <td style="text-align: left;">{{rosie_type}}</td>
                                        <td style="text-align: left;">{{native_type.__name__}}</td>
                                        <td style="text-align: left;">
                                            <button class="btn btn-primary" style="font-size: 12px;" href="#" data-toggle="tooltip" data-placement="top" title="Rename Column" type="submit" pd_options="modify={{loop.index0}}">
                                                <i class="fa fa-pencil-square-o" aria-hidden="true"></i>
                                            </button>
                                            <button class="btn btn-primary" style="font-size: 12px;" href="#" data-toggle="tooltip" data-placement="top" title="Transform Column" type="submit" pd_script="self.schema.create_transform({{loop.index0}})" pd_options="transform={{loop.index0}}">
                                                <i class="fa fa-magic" aria-hidden="true"></i>
                                            </button>
                                            <button class="btn btn-primary" style="font-size: 12px;" href="#" data-toggle="tooltip" data-placement="top" title="Delete Column" type="submit" pd_refresh>
                                                <i class="fa fa-trash-o fa-lg"></i>
                                                <pd_script type="preRun">
                                                    return confirm("Are you sure you want to delete '{{name}}'?");
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
                        <div class="panel-body" style="height: 300px; overflow-y: scroll;">
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
                    <input class="btn btn-primary" style="font-size: 12px;" pd_options="RosieUI=true" type="button" value="Finish">
                </div>
            """

    @route(modify="*")
    def modify_screen(self, modify):
        return """
        <div class="well">
            <form>
                <div>
                    <input type="search" id="new_name{{prefix}}" name="colname" placeholder="New Column Name...">
                    <br/>
                    <br/>
                    <input class="btn btn-primary" style="font-size: 12px;" pd_options="home=true" type="button" value="Cancel">
                    <button class="btn btn-primary" style="font-size: 12px;" type="submit" pd_script="self.schema.rename_column({{modify}}, '$val(new_name{{prefix}})')" pd_options="home=true">Rename</button>
                </div>
            </form>
        </div>
        """

    @route(transform="*")
    def transform_screen(self, transform):
        return """
        <div class="well" style="width: 100%; height: 100%; overflow: hidden;">
            <H1 style="text-align: center;font-size: 180%;">Transform Selected Column</H1>
            <br>
            <div class="panel panel-primary" style="width: 48%; float: left; margin: 1%;">
                <div class="panel-heading">Build Rosie Pattern to Create New Column(s) From Selected Column</div>
                <div class="panel-body" style="height: 200px; overflow-y: scroll;">
                    <style>
                        p {
                          text-indent: 4.0em;
                        }
                    </style>
                   {% if this.schema.transform.components == None%}
                        <div class="search">
                             Enter Rosie Pattern: <br/>
                             <input type="text" style="width: 250px;" id="pat{{prefix}}" class="searchTerm">
                             <br>
                             <br>
                             <button type="submit" pd_script="self.schema.set_transform_components('$val(pat{{prefix}})')" pd_options="transform={{transform}}">Extract Variables</button>
                             <button type="submit" pd_options="transform={{transform}}">Use Suggestion
                                <pd_script>
self.schema.suggest_destructuring({{transform}})
                                </pd_script>
                             </button>
                        </div>

                    {% else %}
                        <div class="search">
                             Enter Rosie Pattern: <br/>
                             <input type="text" style="width: 250px;" id="pat{{prefix}}" class="searchTerm" value="{{this.schema.toStr(this.schema.transform._pattern._definition)}}" readonly>
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
                <div class="panel-heading">Get Help With Rosie</div>
                <div class="panel-body" style="height: 200px; overflow-y: scroll;">
                    {% if this.schema.transform.components == None%}
                        Enter a Rosie pattern line with variables that correspond to the new column(s) that will be created from the selected columnn. In the next step you will define a pattern for each of the specified variables. See an example with the link below:
                    {% else %}
                        Define a Rosie pattern for each of the extracted variables. See an example with the link below:
                    {% endif %}
                    <!--
                    <table class="table table-bordered table-striped">
                        {%for row in this.schema.rosie_cheat_sheet:%}
                            <tr>
                            {%for col in row:%}
                                <td style="text-align: left;">{{col}}</td>
                            {%endfor%}
                            </tr>
                        {%endfor%}
                    </table>
                    -->
                    <br>
                    <br>
                     <a href="https://github.com/jamiejennings/rosie-pattern-language/blob/master/doc/raisondetre.md">Rosie Documentation</a>
                </div>
            </div>
            <br>
            <br>
            <div class="panel panel-primary" style="width: 48%; float: left; margin: 1%;">
                <div class="panel-heading">Sample of Selected Column</div>
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
                <div class="panel-heading">Sample of New Column(s)</div>
                <div class="panel-body" style="height: 400px; overflow-y: scroll;">
                    {% if this.schema.transform.errors %}
                        <font color = "red">Error Message: <br> Invalid definition for "Indicator_Code"</font>
                        <!--{{this.schema.transform.errors}}-->
                    {% elif this.schema.transform.new_sample_data %}
                        <table class="table table-bordered table-striped">
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
                        </table>
                    {% else %}
                        [Build Rosie pattern to display new column(s)]
                    {% endif %}
                </div>
            </div>
            <div style="margin: 1%;">
                <input class="btn btn-primary" style="font-size: 12px;" pd_options="home=true" type="button" value="Cancel">
                <button class="btn btn-primary" style="font-size: 12px;" type="submit" pd_script="self.schema.commit_new_columns()" pd_options="home=true"" >Commit Columns</button>
            </div>
        </div>
        """
