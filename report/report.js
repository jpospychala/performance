app.controller('DiagramCtrl', function($scope, dataService) {
  var ignoredParams = ['MemTotal', 'bogomips', 'cpu cores', 'model name'];
  $scope.funcs = [
    {name: "min", label: "min", selected: false, fn: function(y) {return d3.min(y); }},
    {name: "max", label: "max", selected: false, fn: function(y) {return d3.max(y); }},
    {name: "avg", label: "avg", selected: false, fn: function(y) {return d3.mean(y).toFixed(4); }},
    {name: "q1", label: "0.25-quantile", selected: false, fn: function(y) {return d3.quantile(y, 0.25); }},
    {name: "q2", label: "0.50-quantile", selected: false, fn: function(y) {return d3.quantile(y, 0.5); }},
    {name: "q3", label: "0.75-quantile", selected: false, fn: function(y) {return d3.quantile(y, 0.75); }},
    {name: "q9", label: "0.90-quantile", selected: false, fn: function(y) {return d3.quantile(y, 0.9).toFixed(4); }},
    {name: "q99", label: "0.99-quantile", selected: false, fn: function(y) {return d3.quantile(y, 0.99).toFixed(4); }},
    {name: "throughput", label: "count/(max-min)", selected: false, fn: function(y,d) {return (y.length/(d.max-d.min)).toFixed(4);}}
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
  $scope.$watch('xFrom', setData);
  $scope.$watch('xLen', setData);

  var d = new Diagram("#seriesDiagram");
  d.drawDots = false;
  var d2 = new Diagram("#aggrDiagram");
  d2.drawLine = false;

  dataService.init().then(function(data) {
    $scope.headers = dataService.getHeaders(data);
    $scope.x = $scope.headers[0];
    $scope.y = $scope.headers[1];
  });

  function switchHeader() {
    $scope.data = dataService.withHeaders($scope.y);
    var newParams = findParams($scope.data);
    if ($scope.params) {
      Object.keys($scope.params).forEach(function(param) {
        if (newParams[param]) {
          var sameAsCurrent = R.intersection(newParams[param].values, $scope.params[param].values);
          if (sameAsCurrent.length == newParams[param].values.length) {
            newParams[param].hide = $scope.params[param].hide;
          }
        }
      });
    }
    $scope.params = newParams;
  }

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
      var ret = {
        params: d.params,
        name: label(d),
        values: values
      };
      var yvalues = values.map(ramda.path('y')).sort();
      $scope.funcs.forEach(function(f) {
        ret[f.name] = f.fn(yvalues, ret);
      });
      return ret;
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
