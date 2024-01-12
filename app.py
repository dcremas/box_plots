from pathlib import Path

import pandas as pd

from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, DataTable, TableColumn, Div, Whisker, Button, CustomJS
from bokeh.plotting import figure, curdoc
from bokeh.transform import factor_cmap

total_days = pd.read_csv('data/cities.csv', encoding="ISO-8859-1")

df_region = total_days[["Region", "Total Days"]].rename(columns={
    "Region": "region", "Total Days": "total_days",
    })

df_subregion = total_days[["Sub Region", "Total Days"]].rename(columns={
    "Sub Region": "sub_region", "Total Days": "total_days",
    })

regions = df_region.region.unique()
sub_regions = df_subregion.sub_region.unique()

# compute quantiles
qs_region = df_region.groupby("region").total_days.quantile([0.25, 0.5, 0.75])
qs_region = qs_region.unstack().reset_index()
qs_region.columns = ["region", "q1", "q2", "q3"]
df_region = pd.merge(df_region, qs_region, on="region", how="left")

qs_subregion = df_subregion.groupby("sub_region").total_days.quantile([0.25, 0.5, 0.75])
qs_subregion = qs_subregion.unstack().reset_index()
qs_subregion.columns = ["sub_region", "q1", "q2", "q3"]
df_subregion = pd.merge(df_subregion, qs_subregion, on="sub_region", how="left")

# compute IQR outlier bounds
iqr_region = df_region.q3 - df_region.q1
df_region["upper"] = df_region.q3 + 1.5*iqr_region
df_region["lower"] = df_region.q1 - 1.5*iqr_region

iqr_subregion = df_subregion.q3 - df_subregion.q1
df_subregion["upper"] = df_subregion.q3 + 1.5*iqr_subregion
df_subregion["lower"] = df_subregion.q1 - 1.5*iqr_subregion

source = ColumnDataSource(total_days)
source_region = ColumnDataSource(df_region)
source_subregion = ColumnDataSource(df_subregion)

p_region = figure(x_range=regions, tools="",
                  toolbar_location=None,
                  title="Headache Days distribution by US Region",
                  background_fill_color="#eaefef",
                  height=600, width=400, 
                  y_axis_label="Headache Days",
                  margin=(10, 25, 10, 25))

p_subregion = figure(x_range=sub_regions, tools="",
                  toolbar_location=None,
                  title="Headache Days distribution by US Sub Region",
                  background_fill_color="#eaefef",
                  height=600, width=800, 
                  y_axis_label="Headache Days",
                  margin=(10, 25, 10, 25),
                  sizing_mode="stretch_width")

# outlier range
whisker_region = Whisker(base="region", upper="upper", lower="lower", source=source_region)
whisker_region.upper_head.size = whisker_region.lower_head.size = 20
p_region.add_layout(whisker_region)

whisker_subregion = Whisker(base="sub_region", upper="upper", lower="lower", source=source_subregion)
whisker_subregion.upper_head.size = whisker_subregion.lower_head.size = 20
p_subregion.add_layout(whisker_subregion)

# quantile boxes
cmap_region = factor_cmap("region", "TolRainbow7", regions)
p_region.vbar("region", 0.7, "q2", "q3", source=source_region, color=cmap_region, line_color="black")
p_region.vbar("region", 0.7, "q1", "q2", source=source_region, color=cmap_region, line_color="black")

cmap_subregion = factor_cmap("sub_region", "TolRainbow7", sub_regions)
p_subregion.vbar("sub_region", 0.7, "q2", "q3", source=source_subregion, color=cmap_subregion, line_color="black")
p_subregion.vbar("sub_region", 0.7, "q1", "q2", source=source_subregion, color=cmap_subregion, line_color="black")

# outliers
outliers_region = df_region[~df_region.total_days.between(df_region.lower, df_region.upper)]
p_region.scatter("region", "total_days", source=outliers_region, size=6, color="black", alpha=0.3)

outliers_subregion = df_subregion[~df_subregion.total_days.between(df_subregion.lower, df_subregion.upper)]
p_subregion.scatter("sub_region", "total_days", source=outliers_subregion, size=6, color="black", alpha=0.3)

columns = [
        TableColumn(field="Station Name", title="Station Name"),
        TableColumn(field="Region", title="Region"),
        TableColumn(field="Sub Region", title="Sub Region"),
        TableColumn(field="State", title="State"),
        TableColumn(field="Year", title="Year"),
        TableColumn(field="Total Days", title="Total Days"),
    ]

data_table = DataTable(source=source, columns=columns, width=800, height=600,
                       margin=(10, 250, 25, 250),
                       sizing_mode="stretch_width")

desc = Div(text=(Path(__file__).parent / "description.html").read_text("utf8"), sizing_mode="stretch_width",
           margin=(10, 25, 10, 25))

hyperlink_div = Div(
    text="""<a href="https://dataviz.dustincremascoli.com">Go back to Data Visualizations Main Page</a>""",
    width=400, height=25,
    margin=(10, 10, 10, 25)
    )

button = Button(label="Click to Download data to a .csv file",
                button_type="success",
                margin=(40, 5, 10, 250))

button.js_on_event(
    "button_click",
    CustomJS(
        args=dict(source=source),
        code=(Path(__file__).parent / "download.js").read_text("utf8"),
    ),
)

p_region.xgrid.grid_line_color = None
p_region.axis.major_label_text_font_size="10px"
p_region.axis.axis_label_text_font_size="10px"

p_subregion.xgrid.grid_line_color = None
p_subregion.axis.major_label_text_font_size="8px"
p_subregion.axis.axis_label_text_font_size="10px"

curdoc().add_root(column(desc,
                         hyperlink_div,
                         row(p_region, p_subregion, sizing_mode="inherit"),
                         button,
                         data_table,
                         sizing_mode="stretch_width"))
