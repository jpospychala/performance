var app = angular.module('app', []);
app.controller('DiagramCtrl', function($scope) {
  var ignoredParams = ['MemTotal', 'bogomips', 'cpu cores', 'model name'];
  $scope.funcs = [
    {name: "min", label: "min", selected: false},
    {name: "max", label: "max", selected: false},
    {name: "avg", label: "avg", selected: false},
    {name: "q1", label: "0.25-quantile", selected: false},
    {name: "q2", label: "0.50-quantile", selected: false},
    {name: "q3", label: "0.75-quantile", selected: false},
    {name: "q9", label: "0.90-quantile", selected: false},
    {name: "q99", label: "0.99-quantile", selected: false}
  ];
  $scope.statisticFuncsSelected = {};
  $scope.params = {};
  $scope.showSeriesDiagram = false;
  $scope.showAggregateDiagram = true;
  $scope.showSummaryTable = true;
  $scope.xFrom = $scope.xFrom || 0;
  $scope.xLen = $scope.xLen || 1000;
  $scope.$watch('x', setData);
  $scope.$watch('y', switchHeader);
  $scope.$watch('interpolate', setData);
  $scope.$watch('xFrom', setData);
  $scope.$watch('xLen', setData);

  var d = new Diagram("#seriesDiagram");
  var d2 = new Diagram("#aggrDiagram");
  d3.json("result.json", function(error, data) {
    if (error) {
      console.warn(error);
    }
    data = data.filter(function(d) {
      return d.values.length > 0;
    });
    $scope.raw = data;
    $scope.headers = findHeaders(data);
    $scope.x = $scope.headers[0];
    $scope.y = $scope.headers[1];
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
  $scope.toggleAll = function(params, values) {
    if (values.length < params.length) {
      values.splice.apply(values, [0, values.length].concat(params));
    } else {
      values.splice(0, values.length);
    }
    setData();
  }

  function switchHeader() {
    $scope.data = withHeaders($scope.raw, [$scope.y]);
    var newParams = findParams($scope.data);
    if ($scope.params) {
      Object.keys($scope.params).forEach(function(param) {
        if (newParams[param]) {
          newParams[param] = $scope.params[param];
        }
      });
    }
    $scope.params = newParams;
  }

  function setData() {
    if (!$scope.data) {
      return;
    }
    var uniqueParams = Object.keys($scope.params).filter(function(param) {
      return $scope.params[param].values.length - $scope.params[param]
        .hide.length > 1;
    });

    var newData = $scope.data.filter(filterByParams)
      .map(transformToSeries);

    $scope.series = newData;
    $scope.xMin = d3.min(newData, function(c) {
      return d3.min(c.values, ramda.path('x'));
    });
    $scope.xMax = d3.max(newData, function(c) {
      return d3.max(c.values, ramda.path('x'));
    });
    $scope.yMin = d3.min(newData, function(c) {
      return d3.min(c.values, ramda.path('y'));
    });
    $scope.yMax = d3.max(newData, function(c) {
      return d3.max(c.values, ramda.path('y'));
    });

    if ($scope.showSeriesDiagram) {
      d.setData(newData, $scope.x, $scope.y);
    }

    if ($scope.showAggregateDiagram) {
      $scope.seriesByFunc = calculateSeriesByFunc(newData);
      d2.setData($scope.seriesByFunc, $scope.groupBy, $scope.y);
    }

    function calculateSeriesByFunc(data) {
      var out = {};
      data
      .forEach(function(d) {
        $scope.funcs
        .filter(R.path('selected'))
        .forEach(function(f) {
          var significantParams = R.pick(R.keys($scope.params), d.params);
          var serie = {
            params: R.mixin(R.omit([$scope.groupBy], significantParams), {func:f.label}),
            values: []
          };
          var name = hash(serie);
          serie.name = name;
          if (!out[name]) {
            out[name] = serie;
          }
          out[name].values.push({
            x: d.params[$scope.groupBy],
            y: d[f.name]
          });
        });
      });
      return R.values(out).map(function(d) {
        d.values = R.sort(function (a, b) {return a.x - b.x}, d.values);
        return d;
      });
    }

    function label(d) {
      var params = ramda.pick(uniqueParams, d.params);
      return hash(params);
    }

    function hash(params) {
      return (JSON.stringify(params)).replace(/[^ a-zA-Z0-9:,]/g, '');
    }

    function filterByParams(d) {
      var filtered = true;
      Object.keys($scope.params).forEach(function(param) {
        var v = JSON.stringify(d.params[param]);
        filtered = filtered && ($scope.params[param].hide.indexOf(v) ==
          -1);
      });
      filtered = filtered && (d.headers.indexOf($scope.y) > -1);
      filtered = filtered && (d.headers.indexOf($scope.y) > -1);
      return filtered;
    }

    function transformToSeries(d) {
      var xAxis = valueFunc(d, $scope.x);
      var yAxis = valueFunc(d, $scope.y);
      var values = d.values
        .slice(1 * $scope.xFrom, 1 * $scope.xFrom + 1 * $scope.xLen)
        .map(function(d, i) {
          return {
            x: xAxis(d, i),
            y: yAxis(d, i)
          };
        });
      var yvalues = values.map(ramda.path('y')).sort();
      return {
        params: d.params,
        name: label(d),
        min: d3.min(yvalues),
        max: d3.max(yvalues),
        avg: d3.mean(yvalues).toFixed(4),
        q1: d3.quantile(yvalues, 0.25),
        q2: d3.quantile(yvalues, 0.5),
        q3: d3.quantile(yvalues, 0.75),
        q9: d3.quantile(yvalues, 0.9).toFixed(4),
        q99: d3.quantile(yvalues, 0.99).toFixed(4),
        values: values
      };
    }
  }

  function valueFunc(d, name) {
    if (name === 'n') {
      return function(d, i) {
        return i;
      };
    }
    var axis = d.headers.indexOf(name);
    if (axis == -1) {
      return function(d, i) {
        return;
      };
    }
    return function(d, i) {
      return d[axis];
    };
  }

  function withHeaders(data, headers) {
    return ramda.filter(function(d) {
      return ramda.intersection(d.headers, headers).length > 0;
    }, data);
  }

  function findHeaders(data) {
    var headers = ['n'];
    data.forEach(function(d) {
      d.headers.forEach(function(header) {
        if (headers.indexOf(header) == -1) {
          headers.push(header);
        }
      });
    });
    return headers;
  }

  function findParams(data) {
    var params = {};
    data.forEach(function(d) {
      Object.keys(d.params).forEach(function(param) {
        if (ignoredParams.indexOf(param) > -1) {
          return;
        }
        var newVal = JSON.stringify(d.params[param]);
        if (!params[param]) {
          params[param] = {
            values: [newVal],
            hide: [newVal]
          };
        } else if (params[param].values.indexOf(newVal) == -1) {
          params[param].values.push(newVal);
          params[param].hide.push(newVal);
        }
      });
    });
    Object.keys(params).forEach(function(param) {
      if (params[param].values.length <= 1) {
        delete params[param];
      }
    });
    return params;
  };
});
