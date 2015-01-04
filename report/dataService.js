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
      if (self.data === undefined) {
        return [];
      }

      return self.data.filter(function(d) {
        var filtered = true;
        Object.keys(filterParams).forEach(function(param) {
          var v = JSON.stringify(d.params[param]);
          filtered = filtered && (filterParams[param].hide.indexOf(v) ==
          -1);
        });
        filtered = filtered && (d.headers.indexOf(headerName) > -1);
        filtered = filtered && (d.headers.indexOf(headerName) > -1);
        return filtered;
      });
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
  };
});
