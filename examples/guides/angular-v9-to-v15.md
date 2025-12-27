# Angular Migration Guide: v9 to v15

Migration steps for updating from Angular 9 to Angular 15.

cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@9 update @angular/cli@9 @angular/core@9"
which should bring you to version 9 of Angular.
Basic
Your project has now been updated to TypeScript 3.8, read more about new compiler checks and errors that might require you to fix issues in your code in the
TypeScript 3.7
or
TypeScript 3.8
announcements.
Basic
Run
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@9 update @angular/material@9"
.
Basic
If you use Angular Universal, run
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@9 update @nguniversal/hapi-engine@9"
or
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@9 update @nguniversal/express-engine@9"
depending on the engine you use. This step may require the
--force
flag if any of your third-party dependencies have not updated the Angular version of their peer dependencies.
Advanced
If your project depends on other Angular libraries, we recommend that you consider updating to their latest version. In some cases this update might be required in order to resolve API incompatibilities. Consult
ng update
or
npm outdated
to learn about your outdated libraries.
Basic
During the update to version 9, your project was transformed as necessary via code migrations in order to remove any incompatible or deprecated API calls from your code base. You can now review these changes, and consult the
Updating to version 9 guide
to learn more about the changes.
Basic
Bound CSS styles and classes previously were applied with a "last change wins" strategy, but now follow a defined precedence. Learn more about
Styling Precedence
.
Medium
If you are a library author and you had a method returning
ModuleWithProviders
(typically via a method named
forRoot()
), you will need to specify the generic type. Learn more
angular.io
Advanced
Support for web tracing framework in Angular was deprecated in version 8. You should stop using any of the
wtf*
APIs. To do performance tracing, we recommend using
browser performance tools
.
Advanced
Remove any
es5BrowserSupport
flags in your
angular.json
and set your
target
to
es2015
in your
tsconfig.json
. Angular now uses your browserslist to determine if an ES5 build is needed.
ng update
will migrate you automatically.
Medium
If you use
ngForm
element selector to create Angular Forms, you should instead use
ng-form
.
Medium
We have updated the
tsconfig.app.json
to limit the files compiled. If you rely on other files being included in the compilation, such as a
typings.d.ts
file, you need to manually add it to the compilation.
Advanced
With Angular 9 Ivy is now the default rendering engine, for any compatibility problems that might arise, read the
Ivy compatibility guide
.
Medium
If you use Angular Universal with
@nguniversal/express-engine
or
@nguniversal/hapi-engine
, several backup files will be created. One of them for
server.ts
. If this file defers from the default one, you may need to copy some changes from the
server.ts.bak
to
server.ts
manually.
Advanced
Angular 9 introduced a global
$localize()
function that needs to be loaded if you depend on Angular's internationalization (i18n). Run
ng add @angular/localize
to add the necessary packages and code modifications. Consult the
$localize Global Import Migration guide
to learn more about the changes.
Basic
In your application projects, you can remove
entryComponents
NgModules and any uses of
ANALYZE_FOR_ENTRY_COMPONENTS
. They are no longer required with the Ivy compiler and runtime. You may need to keep these if building a library that will be consumed by a View Engine application.
Medium
If you use
TestBed.get
, you should instead use
TestBed.inject
. This new method has the same behavior, but is type safe.
Medium
If you use
Angular's i18n support
, you will need to begin using
@angular/localize
. Learn more about the
$localize Global Import Migration
.
Medium
Make sure you are using
Node 12 or later
.
Basic
Run
npx @angular/cli@10 update @angular/core@10 @angular/cli@10
which should bring you to version 10 of Angular.
Basic
Run
npx @angular/cli@10 update @angular/material@10
.
Basic
New projects use the filename
.browserslistrc
instead of
browserslist
.
ng update
will migrate you automatically.
Basic
Angular now requires
tslint
v6,
tslib
v2, and
TypeScript 3.9
.
ng update
will migrate you automatically.
Medium
Stop using
styleext
or
spec
in your Angular schematics.
ng update
will migrate you automatically.
Advanced
In version 10, classes that use Angular features and do not have an Angular decorator are no longer supported.
Read more
.
ng update
will migrate you automatically.
Medium
As of Angular 9, enforcement of @Injectable decorators for DI is stricter and incomplete provider definitions behave differently.
Read more
.
ng update
will migrate you automatically.
Medium
Angular's NPM packages no longer contain jsdoc comments, which are necessary for use with closure compiler (extremely uncommon). This support was experimental and only worked in some use cases. There will be an alternative recommended path announced shortly.
Advanced
If you use Angular forms, inputs of type
number
no longer listen to
change events
(this events are not necessarily fired for each alteration the value), instead listen for an
input events
.
Medium
For Angular forms validation, the
minLength
and
maxLength
validators now verify that the form control's value has a numeric length property, and only validate for length if that's the case.
Medium
The
Angular Package Format
has been updated to remove
esm5
and
fesm5
formats. These are no longer distributed in our npm packages. If you don't use the CLI, you may need to downlevel Angular code to ES5 yourself.
Medium
Warnings about unknown elements are now logged as errors. This won't break your app, but it may trip up tools that expect nothing to be logged via
console.error
.
Medium
Any resolver which returns
EMPTY
will cancel navigation. If you want to allow navigation to continue, you will need to update the resolvers to emit some value, (i.e.
defaultIfEmpty(...)
,
of(...)
, etc).
Advanced
If you use the Angular service worker and rely on resources with
Vary
headers, these headers are now ignored to avoid unpredictable behavior across browsers. To avoid this,
configure
your service worker to avoid caching these resources.
Advanced
You may see
ExpressionChangedAfterItHasBeenChecked
errors that were not detected before when using the
async
pipe. The error could previously have gone undetected because two
WrappedValues
are considered "equal" in all cases for the purposes of the check, even if their respective unwrapped values are not. In version 10,
WrappedValue
has been removed.
Medium
If you have a property binding such as
[val]=(observable | async).someProperty
, this will no longer trigger change detection if the value of
someProperty
is identical to the previous emit. If you rely on this, either manually subscribe and call
markForCheck
as needed or update the binding to ensure the reference changes.
Advanced
If you use either
formatDate()
or
DatePipe
and any of the
b
or
B
format codes, the logic has been updated so that it matches times that are within a day period that spans midnight, so it will now render the correct output, such as at
night
in the case of English.
Advanced
If you use the
UrlMatcher
, the type now reflects that it could always return
null
.
Advanced
For more details about deprecations, automated migrations, and changes visit the
guide angular.io
Basic
For Angular Universal users, if you use
useAbsoluteUrl
to setup
platform-server
, you now need to also specify
baseUrl
.
Medium
Run
ng update @angular/core@11 @angular/cli@11
which should bring you to version 11 of Angular.
Basic
Run
ng update @angular/material@11
.
Basic
Angular now requires
TypeScript 4.0
.
ng update
will migrate you automatically.
Basic
Support for IE9, IE10, and IE mobile has been removed. This was announced in the
v10 update
.
Basic
You can now opt-in to use webpack 5 by using Yarn and adding
"resolutions": {"webpack": "^5.0.0"}
to your
package.json
.
Medium
When generating new projects, you will be asked if you want to enable strict mode. This will configure TypeScript and the Angular compiler for stricter type checking, and apply smaller bundle budgets by default. You can use the
--strict=true
or
--strict=false
to skip the prompt.
Medium
If you use the router, the default value of
relativeLinkResolution
has changed from
legacy
to
corrected
. If your application previously used the default by not specifying a value in the
ExtraOptions
and uses relative links when navigating from children of empty path routes, you will need to update your
RouterModule
's configuration to specifically specify
legacy
for
relativeLinkResolution
. See
the documentation
for more details.
Advanced
In the Angular Router, the options deprecated in v4 for
initialNavigation
have been removed. If you previously used
enabled
or
true
, now choose
enabledNonBlocking
or
enabledBlocking
. If you previously used
false
or
legacy_disabled
, now use
disabled
.
Advanced
In the Angular Router's
routerLink
,
preserveQueryParams
has been removed, use
queryParamsHandling="preserve"
instead.
Medium
If you were accessing the
routerLink
values of
queryParams
,
fragment
or
queryParamsHandling
you might need to relax the typing to also accept
undefined
and
null
.
Advanced
The component view encapsulation option
ViewEncapsulation.Native
has been removed. Use
ViewEncapsulation.ShadowDom
instead.
ng update
will migrate you automatically.
Advanced
If you use i18n, expressions within International Components for Unicode (ICUs) expressions are now type-checked again. This may cause compilation failures if errors are found in expressions that appear within an ICU.
Advanced
Directives in the
@angular/forms
package used to have
any[]
as the type of the expected
validators
and
asyncValidators
arguments in constructors. Now these arguments are properly typed, so if your code relies on form's directive constructor types it may require some updates to improve type safety.
Advanced
If you use Angular Forms, the type of
AbstractFormControl.parent
now includes null.
ng update
will migrate you automatically, but in an unlikely case your code was testing the parent against undefined with strict equality, you'll need to change this to
=== null
instead, since the parent is now explicitly initialized with
null
instead of being left undefined.
Advanced
The rarely used
@angular/platform-webworker
and
@angular/platform-webworker-dynamic
were deprecated in v8 and have been removed. Running parts of Angular in a web worker was an experiment that never worked well for common use cases. Angular still has great support for
Web Workers
.
Advanced
The
slice
pipe now returns null for the undefined input value, which is consistent with the behavior of most pipes.
Advanced
The
keyvalue
pipe has been fixed to report that for input objects that have number keys, the result type will contain the string representation of the keys. This was already the case and the code has simply been updated to reflect this. Please update the consumers of the pipe output if they were relying on the incorrect types. Note that this does not affect use cases where the input values are
Map
s, so if you need to preserve
number
s, this is an effective way.
Advanced
The number pipes (
decimal
,
percent
,
currency
, etc) now explicitly state which types are accepted.
Advanced
The
date
pipe now explicitly states which types are accepted.
Advanced
When passing a date-time formatted string to the
DatePipe
in a format that contains fractions of a millisecond, the milliseconds will now always be rounded down rather than to the nearest millisecond. Most applications will not be affected by this change. If this is not the desired behaviour then consider pre-processing the string to round the millisecond part before passing it to the
DatePipe
.
Advanced
The
async
pipe no longer claims to return undefined for an input that was typed as undefined. Note that the code actually returned null on undefined inputs.
Advanced
The
uppercase
and
lowercase
pipes no longer let falsy values through. They now map both
null
and
undefined
to
null
and raise an exception on invalid input (
0
,
false
,
NaN
). This matches other Angular pipes.
Medium
If you use the router with
NavigationExtras
, new typings allow a variable of type
NavigationExtras
to be passed in, but they will not allow object literals, as they may only specify known properties. They will also not accept types that do not have properties in common with the ones in the
Pick
. If you are affected by this change, only specify properties from the NavigationExtras which are actually used in the respective function calls or use a type assertion on the object or variable:
as NavigationExtras
.
Advanced
In your tests if you call
TestBed.overrideProvider
after TestBed initialization, provider overrides are no longer applied. This behavior is consistent with other override methods (such as
TestBed.overrideDirective
, etc) but they throw an error to indicate that. The check was previously missing in the TestBed.overrideProvider function. If you see this error, you should move
TestBed.overrideProvider
calls before TestBed initialization is completed.
Medium
If you use the Router's RouteReuseStrategy, the argument order has changed. When calling
RouteReuseStrategy#shouldReuseRoute
previously when evaluating child routes, they would be called with the
future
and
current
arguments swapped. If your
RouteReuseStrategy
relies specifically on only the future or current snapshot state, you may need to update the
shouldReuseRoute
implementation's use of
future
and
current
ActivateRouteSnapshots
.
Medium
If you use locale data arrays, this API will now return readonly arrays. If you were mutating them (e.g. calling
sort()
,
push()
,
splice()
, etc) then your code will not longer compile. If you need to mutate the array, you should now take a copy (e.g. by calling
slice()
) and mutate the copy.
Advanced
In change detection,
CollectionChangeRecord
has been removed, use
IterableChangeRecord
instead.
Advanced
If you use Angular Forms with async validators defined at initialization time on class instances of
FormControl
,
FormGroup
or
FormArray
, the status change event was not previously emitted once async validator completed. This has been changed so that the status event is emitted into the
statusChanges
observable. If your code relies on the old behavior, you can filter/ignore this additional status change event.
Medium
Run
ng update @angular/core@12 @angular/cli@12
which should bring you to version 12 of Angular.
Basic
Run
ng update @angular/material@12
.
Basic
Angular now requires
TypeScript 4.2
.
ng update
will update you automatically.
Basic
IE11 support has been deprecated. Find details in the
RFC for IE11 removal
.
Basic
You can no longer use Angular with Node.js version 10 or older
Basic
Change the import of
XhrFactory
from
@angular/common/http
to
@angular/common
.
Medium
If you rely on legacy i18n message IDs use the
localize-migrate
tool to
move away from them
.
Medium
If you are using
emitDistinctChangesOnly
to configure
@ContentChildren
and
@ViewChildren
queries, you may need to update its value to
false
to align with its previous behavior. In v12
emitDistinctChangesOnly
has default value
true
, and in future releases we will remove this configuration option to prevent triggering of unnecessary changes.
Medium
You can run the optional migration for enabling production builds by default
ng update @angular/cli@12 --migrate-only production-by-default
.
Medium
If you  use Angular forms,
min
and
max
attributes on
<input type="number">
will now trigger validation logic.
Advanced
If your app has custom classes that extend
FormArray
or
FormGroup
classes and override the above-mentioned methods, you may need to update your implementation
Advanced
Update zone.js to version 0.11.4.
ng update
will update this dependency automatically.
Advanced
If you extend the
HttpParams
class you may have to update the signature of its method to reflect changes in the parameter types.
Advanced
routerLinkActiveOptions
property of
RouterLinkActive
now has a more specific type. You may need to update code accessing this property to align with the changes.
Advanced
The initializer callbacks now have more specific return types, which may require update of your code if you are getting an
APP_INITIALIZER
instance via
Injector.get
or
TestBed.inject
.
Advanced
The router fragments now could be
null
. Add
null
checks to avoid TypeScript failing with type errors.
Advanced
Make sure you don't rely on
ng.getDirectives
throwing an error if it can't find a directive associated with a particular DOM node.
Advanced
Check out
optimization.styles.inlineCritical
option in your angular.json file. It now defaults to
true
. Remember that the whole
optimization
option can be set as boolean which will set all the suboptions to defaults.
Advanced
Run
ng update @angular/core@13 @angular/cli@13
which should bring you to version 13 of Angular.
Basic
Run
ng update @angular/material@13
.
Basic
Angular now uses TypeScript 4.4, read more about any potential breaking changes:
https://www.typescriptlang.org/docs/handbook/release-notes/typescript-4-4.html
Basic
Make sure you are using
Node 12.20.0 or later
Basic
You can now disable the navigation of a
routerLink
by passing
undefined
and
null
. Previously the
routerLink
directive used to accept these two values as equivalent to an empty string.
Medium
You can no longer specify lazy-loaded routes by setting a string value to
loadChildren
. Make sure you move to dynamic ESM import statements.
Medium
The
activated
observable of
SwUpdate
is now deprecated. To check the activation status of a service worker use the
activatedUpdate
method instead.
Medium
The
available
observable of
SwUpdate
is now deprecated. To get the same information use
versionUpdates
and filter only the
VersionReadyEvent
events.
Medium
The
renderModuleFactory
from
@angular/platform-server
is no longer necessary with Ivy. Use
renderModule
instead.
Medium
We narrowed the type of
AbstractControl.status
to
FormControlStatus
and
AbstractControl.status
to
Observable<FormControlStatus>
.
FormControlStatus
is the union of all possible status strings for form controls.
Advanced
To align with the URI spec, now the URL serializer respects question marks in the query parameters. For example
/path?q=hello?&q2=2
will now be parsed to
{ q:
hello?
, q2: 2 }
Advanced
href
is now an attribute binding. This means that
DebugElement.properties['href']
now returns the
href
value returned by the native element, rather than the internal value of the
href
property of the
routerLink
.
Advanced
SpyLocation
no longer emits the
popstate
event when
location.go
is called. In addition,
simulateHashChange
now triggers both
haschange
and
popstate
. Tests that rely on
location.go
most likely need to now use
simulateHashChange
to capture
popstate
.
Advanced
The router will no longer replace the browser URL when a new navigation cancels an ongoing navigation. Hybrid applications which rely on the
navigationId
being present on initial navigations that were handled by the Angular router should subscribe to
NavigationCancel
events and perform the
location.replaceState
to add
navigationId
to the
Router
state. In addition, tests which assert
urlChanges
on the
SpyLocation
may need to be adjusted to account for the
replaceState
which is no longer triggered.
Advanced
The route package no longer exports
SpyNgModuleFactoryLoader
and
DeprecatedLoadChildren
. In case you use them, make sure you remove their corresponding import statements.
Advanced
Run
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
ng update @angular/core@15 @angular/cli@15
to update your application to Angular v15.
Basic
Run
ng update @angular/material@15
to update the Material components.
Basic
In v15, the Angular compiler prefixes
@keyframes
in CSS with the component's scope. This means that any TypeScript code that relies on
keyframes
names no longer works in v15. Update any such instances to: define keyframes programmatically, use global stylesheets, or change the component's view encapsulation.
Read further
Medium
In your application's
tsconfig.json
file, remove
enableIvy
. In v15, Ivy is the only rendering engine so
enableIvy
is not required.
Basic
Make sure to use decorators in base classes with child classes that inherit constructors and use dependency injection. Such base classes should be decorated with either
@Injectable
or
@Directive
or the compiler returns an error.
Read further
Medium
In v15,
setDisabledState
is always called when a
ControlValueAccessor
is attached. To opt-out of this behavior, use
FormsModule.withConfig
or
ReactiveFormsModule.withConfig
.
Read further
Medium
Applications that use
canParse
should use
analyze
from
@angular/localize/tools
instead. In v15, the
canParse
method was removed from all translation parsers in
@angular/localize/tools
.
Read further
Advanced
Make sure that all
ActivatedRouteSnapshot
objects have a
title
property. In v15, the
title
property is a required property of
ActivatedRouteSnapshot
.
Read further
Basic
If your tests with
RouterOutlet
break, make sure they don't depend on the instantiation order of the corresponding component relative to change detection. In v15,
RouterOutlet
instantiates the component after change detection.
Read further
Advanced
In v15,
relativeLinkResolution
is not configurable in the Router. It was used to opt out of an earlier bug fix that is now standard.
Read further
Basic
Change instances of the
DATE_PIPE_DEFAULT_TIMEZONE
token to use
DATE_PIPE_DEFAULT_OPTIONS
to configure time zones.  In v15, the
DATE_PIPE_DEFAULT_TIMEZONE
token is deprecated.
Read further
Medium
Existing
<iframe>
instances might have security-sensitive attributes applied to them as an attribute or property binding. These security-sensitive attributes can occur in a template or in a directive's host bindings. Such occurrences require an update to ensure compliance with the new and stricter rules about
<iframe>
bindings. For more information, see
the error page
.
Medium
Update instances of
Injector.get()
that use an
InjectFlags
parameter to use an
InjectOptions
parameter. The
InjectFlags
parameter of
Injector.get()
is deprecated in v15.
Read further
Medium
Update instances of
TestBed.inject()
that use an
InjectFlags
parameter to use an
InjectOptions
parameter. The
InjectFlags
parameter of
TestBed.inject()
is deprecated in v15.
Read further
Basic
Using
providedIn: ngModule
for an
@Injectable
and
InjectionToken
is deprecated in v15.
Read further
Medium
Using
providedIn: 'any'
for an
@Injectable
or
InjectionToken
is deprecated in v15.
Read further
Basic
Update instances of the
RouterLinkWithHref
directive to use the
RouterLink
directive. The
RouterLinkWithHref
directive is deprecated in v15.
Read further
Medium
In Angular Material v15, many of the components have been refactored to be based on the official Material Design Components for Web (MDC). This change affected the DOM and CSS classes of many components.
Read further
Basic
After you update your application to v15, visually review your application and its interactions to ensure everything is working as it should.
Basic
Make sure that you are using a supported version of node.js before you upgrade your application. Angular v16 supports node.js versions: v16 and v18.
Basic
Make sure that you are using a supported version of TypeScript before you upgrade your application. Angular v16 supports TypeScript version 4.9.3 or later.
Basic
In the application's project directory, run
