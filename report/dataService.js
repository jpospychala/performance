var app = angular.module('app', []);

app.service('dataService', function($q) {
  var ignoredParams = ['MemTotal', 'bogomips', 'cpu cores', 'model name'];
  return new function() {
    var self = this;

    self.init = function() {
      var deferred = $q.defer();

      d3.json("result.json", function(error, data) {
        if (error) {
          deferred.reject(error);
          return;
        }

        self.data = data;
        deferred.resolve(self.data);
      });

      return deferred.promise;
    };

    self.getHeaders = function(data) {
      var headers = ['n'];
      data.forEach(function(d) {
        d.headers.forEach(function(header) {
          if (headers.indexOf(header) == -1) {
            headers.push(header);
          }
        });
      });
      return headers;
    };


    self.getParamsForHeader = function(headerName) {
      var data = withHeader(headerName);
      return findParams(data);
    };


    self.dataForParams = function(filterParams, headerName) {
      if (Object.keys(filterParams).length == 0) {
        return [];
      }
      if (self.data === undefined) {
        return [];
      }

      return self.data.filter(function(d) {
        var filtered = true;
        Object.keys(filterParams).forEach(function(param) {
          var v = d.params[param];
          filtered = filtered && (filterParams[param][v] === true);
        });
        filtered = filtered && (d.headers.indexOf(headerName) > -1);
        filtered = filtered && (d.headers.indexOf(headerName) > -1);
        return filtered;
      });
    };

    self.getAllValues = function(series, x, y) {
      return $q.all(series.map(function(d) {
        return self.getValues(d, x, y);
      }));
    }

    self.getValues = function(d, x, y) {
      var deferred = $q.defer();
      var i = -1;
      var xGet = valueFunc(x);
      var yGet = valueFunc(y);
      d3.csv('../results/'+d.id+'/'+d.params.task+'.log')
      .row(function (row) {
        i++;
        return {x: +xGet(row), y: +yGet(row) };
        })
      .get(function (error, rows) {
        deferred.resolve(R.mixin(d, {values: rows}));
      });

      return deferred.promise;

      function valueFunc(name) {
        if (name === 'n') {
          return function(d) { return i; };
        }
        return function(d) { return d[name]; };
      };
    };

    function withHeader (header) {
      return ramda.filter(function(d) {
        return d.headers.indexOf(header) > -1;
      }, self.data);
    };

    function findParams(data) {
      var params = {};
      data.forEach(function(d) {
        Object.keys(d.params).forEach(function(param) {
          if (ignoredParams.indexOf(param) > -1) {
            return;
          }
          var newVal = d.params[param];
          if (!params[param]) {
            params[param] = {};
          }
          if (params[param][newVal] === undefined) {
            params[param][newVal] = true;
          }
        });
      });
      Object.keys(params).forEach(function(param) {
        if (Object.keys(params[param]).length <= 1) {
          delete params[param];
        }
      });
      return params;
    };
  };
});
