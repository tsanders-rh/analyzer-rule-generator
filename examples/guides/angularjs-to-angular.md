# AngularJS to Angular Migration Guide

## Overview
This guide covers migrating from AngularJS 1.x to Angular 2+. This is a major framework change requiring significant code transformation.

## Module System

### angular.module() → @NgModule
**AngularJS:**
```javascript
angular.module('app', ['ngRoute', 'ngAnimate']);
```

**Angular:**
```typescript
@NgModule({
  imports: [RouterModule, BrowserAnimationsModule]
})
export class AppModule { }
```

**Detection Pattern:** `angular.module(`

---

## Controllers → Components

### Controller Pattern
**AngularJS:**
```javascript
angular.module('app').controller('ProductController', function($scope) {
  $scope.products = [];
  $scope.addProduct = function() { ... };
});
```

**Angular:**
```typescript
@Component({
  selector: 'product-list',
  templateUrl: './product-list.component.html'
})
export class ProductListComponent {
  products = [];
  addProduct() { ... }
}
```

**Detection Pattern:** `.controller(`

---

## Scope Variables

### $scope Usage
**AngularJS:**
```javascript
function MyController($scope) {
  $scope.name = 'John';
  $scope.updateName = function() { ... };
}
```

**Angular:**
```typescript
export class MyComponent {
  name = 'John';
  updateName() { ... }
}
```

**Detection Pattern:** `$scope.`

---

## Services and Factories

### Service Definition
**AngularJS:**
```javascript
angular.module('app').service('ProductService', function($http) {
  this.getProducts = function() {
    return $http.get('/api/products');
  };
});
```

**Angular:**
```typescript
@Injectable({ providedIn: 'root' })
export class ProductService {
  constructor(private http: HttpClient) {}

  getProducts() {
    return this.http.get('/api/products');
  }
}
```

**Detection Pattern:** `.service(` or `.factory(`

---

## HTTP Service

### $http → HttpClient
**AngularJS:**
```javascript
$http.get('/api/data').success(function(data) {
  $scope.data = data;
}).error(function(err) {
  console.error(err);
});
```

**Angular:**
```typescript
this.http.get('/api/data').subscribe(
  data => this.data = data,
  err => console.error(err)
);
```

**Detection Pattern:** `$http.get`, `$http.post`, `.success(`, `.error(`

---

## Directives → Components

### Directive Definition
**AngularJS:**
```javascript
angular.module('app').directive('myDirective', function() {
  return {
    restrict: 'E',
    template: '<div>{{data}}</div>',
    scope: {
      data: '='
    }
  };
});
```

**Angular:**
```typescript
@Component({
  selector: 'my-directive',
  template: '<div>{{data}}</div>'
})
export class MyDirectiveComponent {
  @Input() data: string;
}
```

**Detection Pattern:** `.directive(`

---

## Filters → Pipes

### Filter Definition
**AngularJS:**
```javascript
angular.module('app').filter('capitalize', function() {
  return function(input) {
    return input.charAt(0).toUpperCase() + input.slice(1);
  };
});
```

**Angular:**
```typescript
@Pipe({ name: 'capitalize' })
export class CapitalizePipe implements PipeTransform {
  transform(value: string): string {
    return value.charAt(0).toUpperCase() + value.slice(1);
  }
}
```

**Detection Pattern:** `.filter(`

---

## Template Syntax

### ng-repeat → *ngFor
**AngularJS:**
```html
<div ng-repeat="item in items">{{item.name}}</div>
```

**Angular:**
```html
<div *ngFor="let item of items">{{item.name}}</div>
```

**Detection Pattern:** `ng-repeat`

### ng-if → *ngIf
**AngularJS:**
```html
<div ng-if="isVisible">Content</div>
```

**Angular:**
```html
<div *ngIf="isVisible">Content</div>
```

**Detection Pattern:** `ng-if`

### ng-show/ng-hide → [hidden]
**AngularJS:**
```html
<div ng-show="isVisible">Content</div>
<div ng-hide="isHidden">Content</div>
```

**Angular:**
```html
<div [hidden]="!isVisible">Content</div>
<div [hidden]="isHidden">Content</div>
```

**Detection Pattern:** `ng-show`, `ng-hide`

### ng-class → [ngClass]
**AngularJS:**
```html
<div ng-class="{active: isActive}">Content</div>
```

**Angular:**
```html
<div [ngClass]="{active: isActive}">Content</div>
```

**Detection Pattern:** `ng-class` (without brackets)

### ng-model → [(ngModel)]
**AngularJS:**
```html
<input ng-model="username">
```

**Angular:**
```html
<input [(ngModel)]="username">
```

**Detection Pattern:** `ng-model` (without brackets/parens)

### ng-click → (click)
**AngularJS:**
```html
<button ng-click="doAction()">Click</button>
```

**Angular:**
```html
<button (click)="doAction()">Click</button>
```

**Detection Pattern:** `ng-click`

### ng-src → [src]
**AngularJS:**
```html
<img ng-src="{{imageUrl}}">
```

**Angular:**
```html
<img [src]="imageUrl">
```

**Detection Pattern:** `ng-src`

### ng-href → [href]
**AngularJS:**
```html
<a ng-href="{{linkUrl}}">Link</a>
```

**Angular:**
```html
<a [href]="linkUrl">Link</a>
```

**Detection Pattern:** `ng-href`

---

## Routing

### ngRoute → Router
**AngularJS:**
```javascript
angular.module('app').config(function($routeProvider) {
  $routeProvider
    .when('/home', {
      templateUrl: 'home.html',
      controller: 'HomeController'
    });
});
```

**Angular:**
```typescript
const routes: Routes = [
  { path: 'home', component: HomeComponent }
];

@NgModule({
  imports: [RouterModule.forRoot(routes)]
})
export class AppRoutingModule { }
```

**Detection Pattern:** `$routeProvider`, `$route`

### ui-router → Router
**AngularJS:**
```javascript
$stateProvider.state('home', {
  url: '/home',
  templateUrl: 'home.html',
  controller: 'HomeController'
});
```

**Angular:**
```typescript
const routes: Routes = [
  { path: 'home', component: HomeComponent }
];
```

**Detection Pattern:** `$stateProvider`, `ui-sref`

---

## Dependency Injection

### Function Annotation
**AngularJS:**
```javascript
angular.module('app').controller('MyCtrl', ['$scope', '$http', function($scope, $http) {
  // ...
}]);
```

**Angular:**
```typescript
@Component({ ... })
export class MyComponent {
  constructor(private http: HttpClient) { }
}
```

**Detection Pattern:** Array-style DI annotation with strings

---

## Promises

### $q → RxJS
**AngularJS:**
```javascript
function getData($q, $http) {
  var deferred = $q.defer();
  $http.get('/api').success(function(data) {
    deferred.resolve(data);
  });
  return deferred.promise;
}
```

**Angular:**
```typescript
getData(): Observable<any> {
  return this.http.get('/api');
}
```

**Detection Pattern:** `$q.defer`, `deferred.promise`, `deferred.resolve`, `deferred.reject`

---

## Watch and Digest

### $watch → Component lifecycle
**AngularJS:**
```javascript
$scope.$watch('value', function(newVal, oldVal) {
  console.log('Value changed');
});
```

**Angular:**
```typescript
ngOnChanges(changes: SimpleChanges) {
  if (changes['value']) {
    console.log('Value changed');
  }
}
```

**Detection Pattern:** `$scope.$watch`, `$scope.$apply`, `$scope.$digest`

---

## Events

### $broadcast/$emit → EventEmitter
**AngularJS:**
```javascript
$scope.$broadcast('event-name', data);
$scope.$on('event-name', function(event, data) { });
```

**Angular:**
```typescript
@Output() eventName = new EventEmitter<any>();
this.eventName.emit(data);
```

**Detection Pattern:** `$broadcast`, `$emit`, `$on`

---

## Interpolation

### {{}} Binding
**AngularJS:**
```html
<div>{{ctrl.name}}</div>
```

**Angular:**
```html
<div>{{name}}</div>
```

**Detection Pattern:** `{{ctrl.`, controller aliases in templates

---

## Root Scope

### $rootScope → Services
**AngularJS:**
```javascript
$rootScope.globalData = 'value';
```

**Angular:**
```typescript
@Injectable({ providedIn: 'root' })
export class GlobalDataService {
  globalData = 'value';
}
```

**Detection Pattern:** `$rootScope`

---

## Timeout and Interval

### $timeout → setTimeout/RxJS timer
**AngularJS:**
```javascript
$timeout(function() {
  $scope.message = 'Updated';
}, 1000);
```

**Angular:**
```typescript
setTimeout(() => {
  this.message = 'Updated';
}, 1000);
```

**Detection Pattern:** `$timeout`, `$interval`

---

## Location Service

### $location → Router/Location
**AngularJS:**
```javascript
$location.path('/new-path');
var path = $location.path();
```

**Angular:**
```typescript
this.router.navigate(['/new-path']);
const path = this.location.path();
```

**Detection Pattern:** `$location.path`, `$location.url`

---

## Bootstrap

### Manual Bootstrap
**AngularJS:**
```javascript
angular.element(document).ready(function() {
  angular.bootstrap(document, ['app']);
});
```

**Angular:**
```typescript
platformBrowserDynamic().bootstrapModule(AppModule);
```

**Detection Pattern:** `angular.bootstrap`, `angular.element(document).ready`

---

## Summary

This migration requires:
1. Converting JavaScript to TypeScript
2. Replacing angular.module with @NgModule
3. Converting controllers to components
4. Removing $scope usage
5. Updating template directives
6. Migrating services to use Injectable
7. Replacing $http with HttpClient
8. Converting filters to pipes
9. Updating routing configuration
10. Replacing promises with observables
