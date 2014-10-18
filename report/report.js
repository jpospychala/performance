
function Diagram() {
  var self = this;

  var margin = {top: 20, right: 300, bottom: 30, left: 50},
      width = 1260 - margin.left - margin.right,
      height = 500 - margin.top - margin.bottom;

  var parseDate = d3.time.format("%Y%m%d").parse;

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

  var line = d3.svg.line()
      .interpolate("linear")
      .x(function(d) { return x(d.x); })
      .y(function(d) { return y(d.y); });

  var svg = d3.select("body").append("svg")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
    .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

  var label = function(d) {
    var params = self.uniqueParams ? ramda.pick(self.uniqueParams, d.params) : d.params;
    return (d.params.task+' '+JSON.stringify(params)).replace(/[^ a-zA-Z0-9:,]/g, '');
  };

  self.setData = function(data, xName, yName) {
    self.data = data;
    self.xName = xName;
    self.yName = yName;
    self.draw();
  }

  self.draw = function draw() {
    var data = self.data;
    color.domain(data.map(label));

    var series = color.domain().map(function(name) {
      var d = data.filter(function(d) {return label(d) === name;})[0];
      var xAxis = d.headers.indexOf(self.xName);
      var yAxis = d.headers.indexOf(self.yName);
      if (xAxis == -1) xAxis = false;
      if (yAxis == -1) yAxis = false;
      return {
        name: name,
        values: d.values
        .map(function(d, i) {return {x: (xAxis ? d[xAxis] : i), y: (yAxis? d[yAxis] : i)}; })
      };
    });

    x.domain([
      d3.min(series, function(c) { return d3.min(c.values, ramda.path('x')); }),
      d3.max(series, function(c) { return d3.max(c.values, ramda.path('x')); })
    ]);

    y.domain([
      d3.min(series, function(c) { return d3.min(c.values, ramda.path('y')); }),
      d3.max(series, function(c) { return d3.max(c.values, ramda.path('y')); })
    ]);

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

var app = angular.module('app', []);
app.controller('DiagramCtrl', function($scope) {
  $scope.params = {};
  var d = new Diagram();
  d3.json("result.json", function(error, data) {
    if (error) {
      console.warn(error);
    }
    data = data.filter(function(d) {return d.values.length > 0; });
    setControls(data);
    $scope.data = data;
    d.uniqueParams = Object.keys($scope.params);
    d.setData(data, $scope.x, $scope.y);
    $scope.$apply();
  });

  $scope.toggle = function(param, values) {
    var idx = values.indexOf(param);
    if (idx == -1) {
      values.push(param);
    } else {
      values.splice(idx, 1);
    }
    setData();
  };

  function setData() {
    if (!$scope.data) {
      return;
    }
    var newData = $scope.data.filter(function(d) {
      var filtered = true;
      Object.keys($scope.params).forEach(function(param) {
        var v= JSON.stringify(d.params[param]);
        filtered = filtered && ($scope.params[param].hide.indexOf(v) == -1);
      });
      return filtered;
    });
    d.setData(newData, $scope.x, $scope.y);
  }

  $scope.$watch('x', setData);
  $scope.$watch('y', setData);

  function setControls(data) {
    var params = {};
    var headers = ['n'];
    data.forEach(function(d) {
      d.headers.forEach(function(header) {
        if (headers.indexOf(header) == -1) {
          headers.push(header);
        }
      });
      Object.keys(d.params).forEach(function(param) {
        var newVal = JSON.stringify(d.params[param]);
        if (! params[param]) {
          params[param] = {values: [newVal], hide: []};
        } else if (params[param].values.indexOf(newVal) == -1) {
          params[param].values.push(newVal);
        }
      });
    });
    Object.keys(params).forEach(function(param) {
      if (params[param].values.length <= 1) {
        delete params[param];
      }
    });
    $scope.params = params;
    $scope.headers = headers;
    $scope.x = headers[0];
    $scope.y = headers[1];
  };
});