app.controller('DiagramCtrl', function($scope, dataService) {
  $scope.funcs = [
    {name: "min", label: "min", selected: false },
    {name: "max", label: "max", selected: false },
    {name: "mean", label: "mean", selected: false },
    {name: "q1", label: "0.25-quantile", selected: false },
    {name: "q2", label: "0.50-quantile", selected: false },
    {name: "q3", label: "0.75-quantile", selected: false },
    {name: "q9", label: "0.90-quantile", selected: false },
    {name: "q99", label: "0.99-quantile", selected: false },
    {name: "throughput", label: "count/(max-min)", selected: false }
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

  dataService.init().then(function(data) {
    $scope.headers = dataService.getHeaders(data);
    $scope.x = $scope.headers[0];
    $scope.y = $scope.headers[1];
  });

  function switchHeader() {
    var newParams = dataService.getParamsForHeader($scope.y);
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
    var uniqueParams = Object.keys($scope.params).filter(function(param) {
      return $scope.params[param].values.length - $scope.params[param]
        .hide.length > 1;
    });

    var newData = dataService.dataForParams($scope.params, $scope.y)
      .map(transformToSeries);

    $scope.series = newData;

    if ($scope.showSeriesDiagram) {
      d.setData(newData, $scope.x, $scope.y);
    }

    if ($scope.showAggregateDiagram) {
      $scope.seriesByFunc = calculateSeriesByFunc(newData);
      d2.setData($scope.seriesByFunc, $scope.groupBy, $scope.y);
    }

    function calculateSeriesByFunc(data) {
      var out = {};
      var funcs = $scope.funcs.filter(R.path('selected'));
      data
      .forEach(function(d) {
        funcs
        .forEach(function(f) {
          var significantParams = R.pick(uniqueParams, R.omit([$scope.groupBy], d.params));
          if (funcs.length > 1) {
            significantParams = R.mixin(significantParams, {func:f.label});
          }
          var serie = {
            params: significantParams,
            values: []
          };
          var name = hash(serie.params);
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
      var params = R.pick(uniqueParams, d.params);
      return hash(params);
    }

    function hash(params) {
      return (JSON.stringify(params)).replace(/[^ a-zA-Z0-9:,]/g, '');
    }


    function transformToSeries(d) {
      var ret = {
        params: d.params,
        name: label(d)
      };

      //var xAxis = valueFunc(d, $scope.x);
      //var yAxis = valueFunc(d, $scope.y);
      //var values = d.values
      //  .slice(1 * $scope.xFrom, 1 * $scope.xFrom + 1 * $scope.xLen)
      //  .map(function(d, i) {
      //    return {
      //      x: xAxis(d, i),
      //      y: yAxis(d, i)
      //    };
      //  });

      var headerN = d.headers.indexOf($scope.y);
      if (headerN > -1) {
        $scope.funcs.forEach(function(f) {
          ret[f.name] = d.stats[headerN][f.name];
        });
      }
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
});
