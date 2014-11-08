function Diagram() {
  var self = this;
  self.interpolate = 'linear';

  var margin = {top: 20, right: 300, bottom: 30, left: 50},
      width = 1260 - margin.left - margin.right,
      height = 500 - margin.top - margin.bottom;

  var x = d3.scale.linear()
      .range([0, width]);

  var y = d3.scale.linear()
      .range([height, 0]);

  var color = d3.scale.category10();

  var xAxis = d3.svg.axis()
      .scale(x)
      .orient("bottom");

  var yAxis = d3.svg.axis()
      .scale(y)
      .orient("left");

  var svg = d3.select("#diagram").append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  self.setData = function(data, xName, yName, interpolate, range) {
    self.data = data;
    self.xName = xName;
    self.yName = yName;
    self.range = range;
    self.interpolate = interpolate;
    self.range = range;
    self.draw();
  }

  self.draw = function draw() {

    var line = d3.svg.line()
        .interpolate(self.interpolate)
        .x(function(d) { return x(d.x); })
        .y(function(d) { return y(d.y); });

    var data = self.data;
    color.domain(data.map(function(d) { return d.name; }));

    var series = color.domain().map(function(name) {
      var d = data.filter(function(d) {return d.name === name;})[0];
      return { name: name, values: d.values };
    });

    x.domain([
      d3.min(series, function(c) { return d3.min(c.values, ramda.path('x')); }),
      d3.max(series, function(c) { return d3.max(c.values, ramda.path('x')); })]);
    y.domain([self.range.yMin, self.range.yMax]);

    svg.selectAll("*").remove();
    svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis)
      .append("text")
        .attr("y", 21)
        .attr("dy", ".71em")
        .attr("x", (width+50)/2)
        .style("text-anchor", "end")
        .text(self.xName);

    svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
      .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text(self.yName);

    var serie = svg.selectAll(".serie")
        .data(series)
      .enter().append("g")
        .attr("class", "serie");

    serie.append("path")
        .attr("class", "line")
        .attr("d", function(d) { return line(d.values); })
        .style("stroke", function(d) { return color(d.name); });

    serie.append("text")
        .attr("class", "legend")
        .attr("x", width + 10)
        .attr("y", function(d, i) { return (i * 19) + 5; })
        .style("fill", function(d) { return color(d.name); })
        .text(ramda.path('name'));
  }
}