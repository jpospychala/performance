
var app = angular.module('app', []);
app.controller('DiagramCtrl', function($scope) {
  var ignoredParams = ['MemTotal', 'bogomips', 'cpu cores', 'model name'];
  $scope.params = {};
  $scope.interpolates = ['linear', 'step', 'basis', 'bundle', 'cardinal'];
  $scope.interpolate = 'linear';
  $scope.xFrom = $scope.xFrom || 0;
  $scope.xLen = $scope.xLen || 1000;
  $scope.$watch('x', switchHeader);
  $scope.$watch('y', switchHeader);
  $scope.$watch('interpolate', setData);
  $scope.$watch('xFrom', setData);
  $scope.$watch('xLen', setData);

  var d = new Diagram();
  d3.json("result.json", function(error, data) {
    if (error) {
      console.warn(error);
    }
    data = data.filter(function(d) {return d.values.length > 0; });
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
    $scope.data = withHeaders($scope.raw, [$scope.x, $scope.y]);
    var newParams = findParams($scope.data);
    if ($scope.params) {
      Object.keys($scope.params).forEach(function (param) {
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
      return $scope.params[param].values.length - $scope.params[param].hide.length > 1;
    });

    var newData = $scope.data.filter(filterByParams)
    .map(transformToSeries);

    $scope.series = newData;
    $scope.xMin = d3.min(newData, function(c) { return d3.min(c.values, ramda.path('x')); });
    $scope.xMax = d3.max(newData, function(c) { return d3.max(c.values, ramda.path('x')); });
    $scope.yMin = d3.min(newData, function(c) { return d3.min(c.values, ramda.path('y')); });
    $scope.yMax = d3.max(newData, function(c) { return d3.max(c.values, ramda.path('y')); });
    var range = R.pick(['xMin', 'xMax', 'yMin', 'yMax'], $scope);

    d.setData(newData, $scope.x, $scope.y, $scope.interpolate, range);

    function label(d) {
      var params = ramda.pick(uniqueParams, d.params);
      return (JSON.stringify(params)).replace(/[^ a-zA-Z0-9:,]/g, '');
    }

    function filterByParams(d) {
      var filtered = true;
      Object.keys($scope.params).forEach(function(param) {
        var v= JSON.stringify(d.params[param]);
        filtered = filtered && ($scope.params[param].hide.indexOf(v) == -1);
      });
      filtered = filtered && (d.headers.indexOf($scope.y) > -1);
      filtered = filtered && (d.headers.indexOf($scope.y) > -1);
      return filtered;
    }

    function transformToSeries(d) {
      var xAxis = valueFunc(d, $scope.x);
      var yAxis = valueFunc(d, $scope.y);
      var values = d.values
      .slice(1*$scope.xFrom, 1*$scope.xFrom+1*$scope.xLen)
      .map(function(d, i) {
        return {x: xAxis(d, i), y: yAxis(d, i)}; });
      var yvalues = values.map(ramda.path('y')).sort();
      return {
        params: ramda.pick(uniqueParams, d.params),
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
      return function(d, i) { return i; };
    }
    var axis = d.headers.indexOf(name);
    if (axis == -1) {
      return function(d, i) { return; };
    }
    return function(d, i) { return d[axis]; };
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
        if (! params[param]) {
          params[param] = {values: [newVal], hide: [newVal]};
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
