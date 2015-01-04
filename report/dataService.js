var app = angular.module('app', []);

app.service('dataService', function($q) {
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


    self.withHeaders = function (header) {
      return ramda.filter(function(d) {
        return d.headers.indexOf(header) > -1;
      }, self.data);
    }
  };
});
