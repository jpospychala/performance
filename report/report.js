app.controller('DiagramCtrl', function($scope, dataService, $location) {
  $scope.R = R;
  $scope.l12n =
  $scope.human = function(msg) {
    var h = {
      'n': 'sent messages (n)',
      'count/(max-min)': 'messages/ms'
    };
    return h[msg] || msg;
  }
  $scope.funcs = [
    {name: "min", label: "min", selected: false },
    {name: "max", label: "max", selected: false },
    {name: "mean", label: "mean", selected: false },
    {name: "stddev", label: "stddev", selected: false },
    {name: "q1", label: "0.25-quantile", selected: false },
    {name: "q2", label: "0.50-quantile", selected: false },
    {name: "q3", label: "0.75-quantile", selected: false },
    {name: "q9", label: "0.90-quantile", selected: false },
    {name: "q99", label: "0.99-quantile", selected: false },
    {name: "throughput", label: "count/(max-min)", selected: false }
  ];

  var opts = $location.search();
  $scope.params = {};
  $scope.seriesd = opts.seriesd || false;
  $scope.aggrd = opts.aggrd || false;
  $scope.tbl = opts.tbl || false;
  $scope.locked = opts.locked || false;
  $scope.groupBy = opts.groupBy;
  $scope.loading = true;

  $scope.funcs.forEach(function(f) {
    if (opts[f.name]) {
      f.selected = true;
    }
  });

  var d = new Diagram("#seriesDiagram");
  d.drawDots = false;
  var d2 = new Diagram("#aggrDiagram");

  dataService.init().then(function(data) {
    $scope.headers = dataService.getHeaders(data);
    $scope.headersX = ['n', 'time (ms)'];
    $scope.x = opts.x || $scope.headers[0];
    $scope.y = opts.y || $scope.headers[1];

    $scope.$watch('y', switchHeader);
    $scope.$watch('x', setData);
    $scope.loading = false;
  });

  function switchHeader() {
    var newParams = dataService.getParamsForHeader($scope.y);
    if ($scope.params) {
      Object.keys($scope.params).forEach(function(param) {
        if (newParams[param]) {
          var sameAsCurrent = R.intersection(Object.keys(newParams[param]), Object.keys($scope.params[param]));
          if (sameAsCurrent.length == Object.keys(newParams[param]).length) {
            Object.keys(newParams[param]).forEach(function (key) {
              newParams[param][key] = $scope.params[param][key];
            });
          }
        }
      });
    }

    Object.keys(newParams).forEach(function(param) {
      Object.keys(newParams[param]).forEach(function(key) {
        newParams[param][key] = (opts[param+key] === true);
      });
    });
    $scope.params = newParams;
  }

  $scope.truthy = function(objWithProps) {
    return R.toPairs(objWithProps).filter(function(prop) {
      return prop[1] === true;
    })
    .map(R.head);
  }
  $scope.selectedFuncs = function() {
    return $scope.funcs.filter(R.path('selected')).map(R.path('label')).join(' and ');
  }
  $scope.toggleLock = function() {
    $scope.locked = !$scope.locked;
    setSearch();
  }

  $scope.toggle = function(param, key, value) {
    $scope.params[param][key] = !value;
    setData();
  };
  $scope.toggleAll = function(param) {
    var truthyCount = 0;
    Object.keys($scope.params[param]).forEach(function(key) {
      truthyCount += ($scope.params[param][key] ? 1 : 0);
    });
    var newVal = (truthyCount < Object.keys($scope.params[param]).length)
    Object.keys($scope.params[param]).forEach(function(key) {
      $scope.params[param][key] = newVal;
    });
    setData();
  }

  function setData() {
    $scope.uniqueParams = Object.keys($scope.params).filter(function(param) {
      return R.values($scope.params[param]).filter(R.eq(true)).length > 1;
    });

    var newData = dataService.dataForParams($scope.params, $scope.y)
      .map(transformToSeries);

    if ($scope.tbl) {
      $scope.series = newData;
    }

    if ($scope.aggrd) {
      $scope.seriesByFunc = calculateSeriesByFunc(newData);
      d2.setData($scope.seriesByFunc, $scope.groupBy, $scope.y);
    }

    if ($scope.seriesd) {
      dataService.getAllValues(newData, $scope.x, $scope.y)
      .then(function(newData) {
        d.setData(newData, $scope.x, $scope.y);
      });
    }

    setSearch();

    function calculateSeriesByFunc(data) {
      var out = {};
      var funcs = $scope.funcs.filter(R.path('selected'));
      data
      .forEach(function(d) {
        funcs
        .forEach(function(f) {
          var significantParams = R.pick($scope.uniqueParams, R.omit([$scope.groupBy], d.params));
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
      var params = R.pick($scope.uniqueParams, d.params);
      return hash(params);
    }

    function hash(params) {
      return (JSON.stringify(params)).replace(/[^ a-zA-Z0-9:,]/g, '');
    }

    function transformToSeries(d) {
      var ret = {
        id: d.id,
        params: d.params,
        name: label(d)
      };

      var headerN = d.headers.indexOf($scope.y);
      if (headerN > -1) {
        $scope.funcs.forEach(function(f) {
          ret[f.name] = d.stats[headerN][f.name];
        });
      }
      return ret;
    }
  }

  function setSearch() {
    var opts = {
      x: $scope.x,
      y: $scope.y,
    };
    ['seriesd', 'aggrd', 'tbl', 'locked', 'groupBy'].forEach(function(key) {
      if ($scope[key]) {
        opts[key] = true;
      }
    });
    Object.keys($scope.params)
    .sort()
    .forEach(function(p) {
      Object.keys($scope.params[p]).forEach(function(key) {
        if ($scope.params[p][key]) {
          opts[p+key]=true;
        }
      });
    });
    $scope.funcs.forEach(function(f) {
      if (f.selected) {
        opts[f.name] = true;
      }
    });
    $location.search(opts);
  }
});
