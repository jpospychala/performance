
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

  var svg = d3.select("body").append("svg")
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

var app = angular.module('app', []);
app.controller('DiagramCtrl', function($scope) {
  $scope.params = {};
  $scope.interpolates = ['linear', 'step', 'basis', 'bundle', 'cardinal'];
  $scope.interpolate = 'linear';
  $scope.xFrom = $scope.xFrom || 0;
  $scope.xLen = $scope.xLen || 1000;
  $scope.$watch('x', setData);
  $scope.$watch('y', setData);
  $scope.$watch('interpolate', setData);
  $scope.$watch('xFrom', setData);
  $scope.$watch('xLen', setData);

  var d = new Diagram();
  d3.json("result.json", function(error, data) {
    if (error) {
      console.warn(error);
    }
    data = data.filter(function(d) {return d.values.length > 0; });
    setControls(data);
    $scope.data = data;
    setData();
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
    var nonDistinctParams = Object.keys($scope.params).filter(function(param) {
      return $scope.params[param].values.length - $scope.params[param].hide.length > 1;
    });

    var newData = $scope.data.filter(function(d) {
      var filtered = true;
      Object.keys($scope.params).forEach(function(param) {
        var v= JSON.stringify(d.params[param]);
        filtered = filtered && ($scope.params[param].hide.indexOf(v) == -1);
      });
      filtered = filtered && (d.headers.indexOf($scope.y) > -1);
      filtered = filtered && (d.headers.indexOf($scope.y) > -1);
      return filtered;
    })
    .map(function(d) {
      var xAxis = valueFunc(d, $scope.x);
      var yAxis = valueFunc(d, $scope.y);
      return {
        name: label(d, nonDistinctParams),
        values: d.values
        .slice(1*$scope.xFrom, 1*$scope.xFrom+$scope.xLen)
        .map(function(d, i) {
          return {x: xAxis(d, i), y: yAxis(d, i)}; })
      };
    });

    $scope.xMin = d3.min(newData, function(c) { return d3.min(c.values, ramda.path('x')); });
    $scope.xMax = d3.max(newData, function(c) { return d3.max(c.values, ramda.path('x')); });
    $scope.yMin = d3.min(newData, function(c) { return d3.min(c.values, ramda.path('y')); });
    $scope.yMax = d3.max(newData, function(c) { return d3.max(c.values, ramda.path('y')); });
    var range = R.pick(['xMin', 'xMax', 'yMin', 'yMax'], $scope);

    d.setData(newData, $scope.x, $scope.y, $scope.interpolate, range);
  }

  function label(d, uniqueParams) {
    var params = uniqueParams ? ramda.pick(uniqueParams, d.params) : d.params;
    return (JSON.stringify(params)).replace(/[^ a-zA-Z0-9:,]/g, '');
  }

  function valueFunc(d, name) {
    if (name === 'n') {
      return function(d, i) { return i; };
    }
    var axis = d.headers.indexOf(name);
    if (axis == -1) {
      return function(d, i) { return; };
    }
    return function(d, i) { return d[axis]; };
  }

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
