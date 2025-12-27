# Angular Migration Guide: v14

Typed forms introduction.

ng update @angular/core@14 @angular/cli@14
which should bring you to version 14 of Angular.
Basic
Run
ng update @angular/material@14
.
Basic
Angular now uses TypeScript 4.6, read more about any potential breaking changes:
https://devblogs.microsoft.com/typescript/announcing-typescript-4-6/
Basic
Make sure you are using
Node 14.15.0 or later
Basic
Form models now require a generic type parameter. For gradual migration you can opt-out using the untyped version of the form model classes.
Medium
Remove
aotSummaries
from
TestBed
since Angular no longer needs them in Ivy.
Medium
If you are using
MatVerticalStepper
or
MatHorizontalStepper
make sure you switch to
MatStepper
.
Medium
Remove headers from JSONP requests. JSONP does not supports headers and if specified the HTTP module will now throw an error rather than ignoring them.
Medium
Resolvers now will take the first emitted value by an observable and after that proceed to navigation to better align with other guards rather than taking the last emitted value.
Medium
The deprecated
angular/cdk/testing/protractor
entry point is now removed.
Advanced
Make sure you specify
chipInput
of
MatChipInputEvent
because it is now required.
Advanced
You need to implement
stateChanges
class member in abstractions using
mixinErrorState
because the mixin no longer provides it.
Advanced
Use
CdkStepper.orientation
instead of
CdkStepper._orientation
.
Advanced
If you are extending or using
CdkStepper
or
MatStepper
in the constructor you should no longer pass the
_document
parameter since it is now removed.
Advanced
Rename the
mat-list-item-avatar
CSS class to
mat-list-item-with-avatar
.
Advanced
Use
MatSelectionListChange.options
rather than
MatSelectionListChange.option
.
Advanced
Use
getChildLoader(MatListItemSection.CONTENT)
rather than
getHarnessLoaderForContent
.
Advanced
If you are using
MatSelectionList
make sure you pass
_focusMonitor
in its constructor because it is now required. Additionally, this class no longer has
tabIndex
property and a
tabIndex
constructor parameter.
Advanced
Update
initialNavigation: 'enabled'
to
initialNavigation: 'enabledBlocking'
.
Advanced
If you are defining routes with
pathMatch
, you may have to cast it to
Route
or
Routes
explicitly.
Route.pathMatch
is no longer compatible with
string
type.
Advanced
The promise returned by
LoadChildrenCallback
now has a stricter type parameter
Type<any>|NgModuleFactory<any>
rather than
any
.
Advanced
The router does no longer schedule redirect navigation within a
setTimeout
. Make sure your tests do not rely on this behavior.
Advanced
Implementing the
LocationStrategy
interface now requires definition of
getState()
.
Advanced
Sending
+
as part of a query no longer requires workarounds since
+
no longer sends a space.
Advanced
Implementing
AnimationDriver
now requires the
getParentElement
method.
Advanced
Invalid route configurations of lazy-loaded modules will now throw an error rather than being ignored.
Advanced
Remove the
resolver
from
RouterOutletContract.activateWith
function and the
resolver
from
OutletContext
class since factory resolvers are no longer needed.
Advanced
Router.initialUrl
accepts only
UrlTree
to prevent a misuse of the API by assigning a
string
value.
Advanced
Make sure that you are using a supported version of node.js before you upgrade your application. Angular v15 supports node.js versions: 14.20.x, 16.13.x and 18.10.x.
Read further
Basic
Make sure that you are using a supported version of TypeScript before you upgrade your application. Angular v15 supports TypeScript version 4.8 or later.
Read further
Basic
In the application's project directory, run
