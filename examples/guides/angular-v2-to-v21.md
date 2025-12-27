Guide to update your Angular application v2.0 -> v21.0
    for
    advanced applications
Before you update
Ensure you don't use
extends OnInit
, or use
extends
with any lifecycle event. Instead use
implements <lifecycle event>.
Basic
Stop using deep imports, these symbols are now marked with ɵ and are not part of our public API.
Advanced
Stop using
Renderer.invokeElementMethod
as this method has been removed. There is not currently a replacement.
Advanced
Stop using
DefaultIterableDiffer
,
KeyValueDiffers#factories
, or
IterableDiffers#factories
Advanced
Update to the new version
Review these changes and perform the actions to update your application.
If you use animations in your application, you should import
BrowserAnimationsModule
from
@angular/platform-browser/animations
in your App
NgModule
.
Basic
Angular began adding a
novalidate
attribute to form elements when you include
FormsModule
. To re-enable native forms behaviors, use
ngNoForm
or add
ngNativeValidate
.
Medium
Replace
RootRenderer
with
RendererFactoryV2
instead.
Advanced
The return value of
upgrade/static/downgradeInjectable
has changed.
Advanced
If you use Animations and tests, add
mods[1].NoopAnimationsModule
to your
TestBed.initTestEnvironment
call.
Advanced
Rename your
template
tags to
ng-template
Basic
Replace any
OpaqueToken
with
InjectionToken
.
Medium
If you call
DifferFactory.create(...)
remove the
ChangeDetectorRef
argument.
Advanced
Stop passing any arguments to the constructor for ErrorHandler
Advanced
If you use ngProbeToken, make sure you import it from @angular/core instead of @angular/platform-browser
Advanced
If you use TrackByFn, instead use TrackByFunction
Advanced
If you rely on the date, currency, decimal, or percent pipes, in 5 you will see minor changes to the format. For applications using locales other than en-us you will need to import it and optionally
locale_extended_fr
from
@angular/common/i18n_data/locale_fr
and registerLocaleData(local).
Basic
Do not rely on
gendir
, instead look at using
skipTemplateCodeGen
. <a href=
https://github.com/angular/angular/issues/19339#issuecomment-332607471
" target="_blank">Read More
Advanced
Replace
downgradeComponent
,
downgradeInjectable
,
UpgradeComponent
, and
UpgradeModule
imported from
@angular/upgrade
. Instead use the new versions in
@angular/upgrade/static
Basic
If you import any animations services or tools from @angular/core, you should import them from @angular/animations
Medium
Replace
ngOutletContext
with
ngTemplateOutletContext
.
Advanced
Replace
CollectionChangeRecord
with
IterableChangeRecord
Advanced
Anywhere you use Renderer, now use Renderer2
Advanced
If you use preserveQueryParams, instead use queryParamsHandling
Advanced
If you use the legacy
HttpModule
and the
Http
service, switch to
HttpClientModule
and the
HttpClient
service. HttpClient simplifies the default ergonomics (you don't need to map to JSON anymore) and now supports typed return values and interceptors. Read more on
angular.dev
.
Basic
If you use DOCUMENT from @angular/platform-browser, you should start to import this from @angular/common
Advanced
Anywhere you use ReflectiveInjector, now use StaticInjector
Advanced
Choose a value of
off
for
preserveWhitespaces
in your
tsconfig.json
under the
angularCompilerOptions
key to gain the benefits of this setting, which was set to
off
by default in v6.
Medium
Make sure you are using
Node 8 or later
Basic
Update your Angular CLI, and migrate the configuration to the
new angular.json format
by running the following:
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@6 update @angular/cli@6 @angular/core@6"
Basic
Update any
scripts
you may have in your
package.json
to use the latest Angular CLI commands. All CLI commands now use two dashes for flags (eg
ng build --prod --source-map
) to be POSIX compliant.
Medium
Update all of your Angular framework packages to v6, and the correct version of RxJS and TypeScript.
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@6 update @angular/cli@6 @angular/core@6"
After the update, TypeScript and RxJS will more accurately flow types across your application, which may expose existing errors in your application's typings
Basic
In Angular Forms,
AbstractControl#statusChanges
now emits an event of
PENDING
when you call
AbstractControl#markAsPending
. Ensure that if you are filtering or checking events from
statusChanges
that you account for the new event when calling
markAsPending
.
Advanced
If you use totalTime from an
AnimationEvent
within a disabled Zone, it will no longer report a time of 0. To detect if an animation event is reporting a disabled animation then the
event.disabled
property can be used instead.
Advanced
Support for using the ngModel input property and ngModelChange event with reactive form directives has been deprecated in v6 and removed in v7.
Advanced
ngModelChange is now emitted after the value/validity is updated on its control instead of before to better match expectations. If you rely on the order of these events, you will need to begin tracking the old value in your component.
Medium
Update Angular Material to the latest version.
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@6 update @angular/material@6"
This will also automatically migrate deprecated APIs.
Basic
If you have TypeScript configured to be strict (if you have set
strict
to
true
in your
tsconfig.json
file), update your
tsconfig.json
to disable
strictPropertyInitialization
or move property initialization from
ngOnInit
to your constructor. You can learn more about this flag on the
TypeScript 2.7 release notes
.
Medium
Remove deprecated RxJS 5 features using
rxjs-tslint auto update rules
For most applications this will mean running the following two commands:
npx rxjs-tslint
rxjs-5-to-6-migrate -p src/tsconfig.app.json
Basic
Once you and all of your dependencies have updated to RxJS 6, remove
rxjs-compat
.
Medium
If you use the Angular Service worker, migrate any
versionedFiles
to the
files
array. The behavior is the same.
Medium
Angular now uses TypeScript 3.1, read more about any potential breaking changes:
https://www.typescriptlang.org/docs/handbook/release-notes/typescript-3-1.html
Basic
Angular has now added support for Node 10:
https://nodejs.org/en/blog/release/v10.0.0/
Basic
Update to v7 of the core framework and CLI by running
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@7 update @angular/cli@7 @angular/core@7"
in your terminal.
Basic
Update Angular Material to v7 by running
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@7 update @angular/material@7"
in your terminal. You should test your application for sizing and layout changes.
Basic
If you use screenshot tests, you'll need to regenerate your screenshot golden files as many minor visual tweaks have landed.
Medium
Stop using
matRippleSpeedFactor
and
baseSpeedFactor
for ripples, using Animation config instead.
Advanced
Update to version 8 of the core framework and CLI by running
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@8 update @angular/cli@8 @angular/core@8"
in your terminal and review and commit the changes.
Basic
Replace
/deep/
with
::ng-deep
in your styles,
read more about angular component styles and ::ng-deep
.
/deep/
and
::ng-deep
both are deprecated but using
::ng-deep
is preferred until the shadow-piercing descendant combinator is
removed from browsers and tools
completely.
Basic
Angular now uses TypeScript 3.4,
read more about errors that might arise from improved type checking
.
Basic
Make sure you are using
Node 10 or later
.
Basic
The CLI's build command now automatically creates a modern ES2015 build with minimal polyfills and a compatible ES5 build for older browsers, and loads the appropriate file based on the browser.  You may opt-out of this change by setting your
target
back to
es5
in your
tsconfig.json
. Learn more on
angular.io
.
Basic
When using new versions of the CLI, you will be asked if you want to opt-in to share your CLI usage data. You can also add your own Google Analytics account. This lets us make better decisions about which CLI features to prioritize, and measure the impact of our improvements. Learn more on
angular.io
.
Basic
If you use
ViewChild
or
ContentChild
, we're updating the way we resolve these queries to give developers more control. You must now specify that change detection should run before results are set. Example:
@ContentChild('foo', {static: false}) foo !: ElementRef;
.
ng update
will update your queries automatically, but it will err on the side of making your queries
static
for compatibility. Learn more on
angular.io
.
Basic
Update Angular Material to version 8 by running
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@8 update @angular/material@8"
in your terminal.
Basic
Instead of importing from
@angular/material
, you should import deeply from the specific component. E.g.
@angular/material/button
.
ng update
will do this automatically for you.
Basic
For lazy loaded modules via the router, make sure you are
using dynamic imports
. Importing via string is removed in v9.
ng update
should take care of this automatically. Learn more on
angular.io
.
Basic
We are deprecating support for
@angular/platform-webworker
, as it has been incompatible with the CLI. Running Angular's rendering architecture in a web worker did not meet developer needs. You can still use web workers with Angular. Learn more in our
web worker guide
. If you have use cases where you need this, let us know at
devrel@angular.io
!
Advanced
We have switched from the native Sass compiler to the JavaScript compiler. To switch back to the native version, install it as a devDependency:
npm install node-sass --save-dev
.
Advanced
If you are building your own Schematics, they have previously been
potentially
asynchronous. As of 8.0, all schematics will be asynchronous.
Advanced
Make sure you are using
Node 10.13 or later
.
Basic
Run
cmd /C "set "NG_DISABLE_VERSION_CHECK=1" && npx @angular/cli@8 update @angular/cli@8 @angular/core@8"
in your workspace directory to update to the latest 8.x version of
@angular/core
and
@angular/cli
and commit these changes.
Basic
You can optionally pass the
--create-commits
(or
-C
) flag to
ng update
commands to create a git commit per individual migration.
Medium
Run
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
ng update @angular/core@16 @angular/cli@16
to update your application to Angular v16.
Basic
Run
ng update @angular/material@16
.
Basic
Make sure that you are using a supported version of Zone.js before you upgrade your application. Angular v16 supports Zone.js version 0.13.x or later.
Basic
The Event union no longer contains
RouterEvent
, which means that if you're using the Event type you may have to change the type definition from
(e: Event)
to
(e: Event|RouterEvent)
Advanced
In addition to
NavigationEnd
the
routerEvent
property now also accepts type
NavigationSkipped
Advanced
Pass only flat arrays to
RendererType2.styles
because it no longer accepts nested arrays
Advanced
You may have to update tests that use
BrowserPlatformLocation
because
MockPlatformLocation
is now provided by default in tests.
Read further
.
Medium
Due to the removal of the Angular Compatibility Compiler (ngcc) in v16, projects on v16 and later no longer support View Engine libraries.
Basic
After bug fixes in
Router.createUrlTree
you may have to readjust tests which mock
ActivatedRoute
.
Read further
Medium
Change imports of
ApplicationConfig
to be from
@angular/core
.
Medium
Revise your code to use
renderModule
instead of
renderModuleFactory
because it has been deleted.
Advanced
Revise your code to use
XhrFactory
from
@angular/common
instead of
XhrFactory
export from
@angular/common/http
.
Medium
If you're running multiple Angular apps on the same page and you're using
BrowserModule.withServerTransition({ appId: 'serverApp' })
make sure you set the
APP_ID
instead since
withServerTransition
is now deprecated.
Read further
Medium
Change
EnvironmentInjector.runInContext
to
runInInjectionContext
and pass the environment injector as the first parameter.
Advanced
Update your code to use
ViewContainerRef.createComponent
without the factory resolver.
ComponentFactoryResolver
has been removed from Router APIs.
Advanced
If you bootstrap multiple apps on the same page, make sure you set unique
APP_IDs
.
Advanced
Update your code to revise
renderApplication
method as it no longer accepts a root component as first argument, but instead a callback that should bootstrap your app.
Read further
Advanced
Update your code to remove any reference to
PlatformConfig.baseUrl
and
PlatformConfig.useAbsoluteUrl
platform-server config options as it has been deprecated.
Advanced
Update your code to remove any reference to
@Directive
/
@Component
moduleId
property as it does not have any effect and will be removed in v17.
Basic
Update imports from
import {makeStateKey, StateKey, TransferState} from '@angular/platform-browser'
to
import {makeStateKey, StateKey, TransferState} from '@angular/core'
Medium
If you rely on
ComponentRef.setInput
to set the component input even if it's the same based on
Object.is
equality check, make sure you copy its value.
Advanced
Update your code to remove any reference to
ANALYZE_FOR_ENTRY_COMPONENTS
injection token as it has been deleted.
Advanced
entryComponents
is no longer available and any reference to it can be removed from the
@NgModule
and
@Component
public APIs.
Basic
ngTemplateOutletContext has stricter type checking which requires you to declare all the properties in the corresponding object.
Read further
.
Medium
Angular packages no longer include FESM2015 and the distributed ECMScript has been updated from 2020 to 2022.
Medium
The deprecated
EventManager
method
addGlobalEventListener
has been removed as it is not used by Ivy.
Advanced
BrowserTransferStateModule
is no longer available and any reference to it can be removed from your applications.
Medium
Update your code to use
Injector.create
rather than
ReflectiveInjector
since
ReflectiveInjector
is removed.
Medium
QueryList.filter
now supports type guard functions. Since the type will be narrowed, you may have to update your application code that relies on the old behavior.
Basic
Make sure that you are using a supported version of node.js before you upgrade your application. Angular v17 supports node.js versions: v18.13.0 and newer
Basic
Make sure that you are using a supported version of TypeScript before you upgrade your application. Angular v17 supports TypeScript version 5.2 or later.
Basic
Make sure that you are using a supported version of Zone.js before you upgrade your application. Angular v17 supports Zone.js version 0.14.x or later.
Basic
In the application's project directory, run
ng update @angular/core@17 @angular/cli@17
to update your application to Angular v17.
Basic
Run
ng update @angular/material@17
.
Basic
Angular now automatically removes styles of destroyed components, which may impact your existing apps in cases you rely on leaked styles. To change this update the value of the
REMOVE_STYLES_ON_COMPONENT_DESTROY
provider to
false
.
Medium
Make sure you configure
setupTestingRouter
,
canceledNavigationResolution
,
paramsInheritanceStrategy
,
titleStrategy
,
urlUpdateStrategy
,
urlHandlingStrategy
, and
malformedUriErrorHandler
in
provideRouter
or
RouterModule.forRoot
since these properties are now not part of the
Router
's public API
Basic
For dynamically instantiated components we now execute
ngDoCheck
during change detection if the component is marked as dirty. You may need to update your tests or logic within
ngDoCheck
for dynamically instantiated components.
Advanced
Handle URL parsing errors in the
UrlSerializer.parse
instead of
malformedUriErrorHandler
because it's now part of the public API surface.
Medium
Change Zone.js deep imports like
zone.js/bundles/zone-testing.js
and
zone.js/dist/zone
to
zone.js
and
zone.js/testing
.
Medium
You may need to adjust your router configuration to prevent infinite redirects after absolute redirects. In v17 we no longer prevent additional redirects after absolute redirects.
Advanced
Change references to
AnimationDriver.NOOP
to use
NoopAnimationDriver
because
AnimationDriver.NOOP
is now deprecated.
Medium
You may need to adjust the equality check for
NgSwitch
because now it defaults to stricter check with
===
instead of
==
. Angular will log a warning message for the usages where you'd need to provide an adjustment.
Basic
Use
update
instead of
mutate
in Angular Signals. For example
items.mutate(itemsArray => itemsArray.push(newItem));
will now be
items.update(itemsArray => [itemsArray, …newItem]);
Advanced
To disable hydration use
ngSkipHydration
or remove the
provideClientHydration
call from the provider list since
withNoDomReuse
is no longer part of the public API.
Medium
If you want the child routes of
loadComponent
routes to inherit data from their parent specify the
paramsInheritanceStrategy
to
always
, which in v17 is now set to
emptyOnly
.
Basic
Make sure that you are using a supported version of node.js before you upgrade your application. Angular v18 supports node.js versions: v18.19.0 and newer
Basic
In the application's project directory, run
ng update @angular/core@18 @angular/cli@18
to update your application to Angular v18.
Basic
Run
ng update @angular/material@18
.
Basic
Update TypeScript to versions 5.4 or newer.
Basic
Replace
async
from
@angular/core
with
waitForAsync
.
Advanced
Remove calls to
matchesElement
because it's now not part of
AnimationDriver
.
Advanced
Import
StateKey
and
TransferState
from
@angular/core
instead of
@angular/platform-browser
.
Medium
Use
includeRequestsWithAuthHeaders: true
in
withHttpTransferCache
to opt-in of caching for HTTP requests that require authorization.
Medium
Update the application to remove
isPlatformWorkerUi
and
isPlatformWorkerApp
since they were part of platform WebWorker which is now not part of Angular.
Advanced
Tests may run additional rounds of change detection to fully reflect test state in the DOM. As a last resort, revert to the old behavior by adding
provideZoneChangeDetection({ignoreChangesOutsideZone: true})
to the TestBed providers.
Medium
Remove expressions that write to properties in templates that use
[(ngModel)]
Medium
Remove calls to
Testability
methods
increasePendingRequestCount
,
decreasePendingRequestCount
, and
getPendingRequestCount
. This information is tracked by ZoneJS.
Advanced
Move any environment providers that should be available to routed components from the component that defines the
RouterOutlet
to the providers of
bootstrapApplication
or the
Route
config.
Medium
When a guard returns a
UrlTree
as a redirect, the redirecting navigation will now use
replaceUrl
if the initial navigation was also using the
replaceUrl
option. If you prefer the previous behavior, configure the redirect using the new
NavigationBehaviorOptions
by returning a
RedirectCommand
with the desired options instead of
UrlTree
.
Advanced
Remove dependencies of
RESOURCE_CACHE_PROVIDER
since it's no longer part of the Angular runtime.
Advanced
In
@angular/platform-server
now
pathname
is always suffixed with
/
and the default ports for http: and https: respectively are 80 and 443.
Advanced
Provide an absolute
url
instead of using
useAbsoluteUrl
and
baseUrl
from
PlatformConfig
.
Medium
Replace the usage of
platformDynamicServer
with
platformServer
. Also, add an
import @angular/compiler
.
Advanced
Remove all imports of
ServerTransferStateModule
from your application. It is no longer needed.
Medium
Route.redirectTo
can now include a function in addition to a string. Any code which reads
Route
objects directly and expects
redirectTo
to be a string may need to update to account for functions as well.
Advanced
Route
guards and resolvers can now return a
RedirectCommand
object in addition to a
UrlTree
and
boolean
. Any code which reads
Route
objects directly and expects only
boolean
or
UrlTree
may need to update to account for
RedirectCommand
as well.
Advanced
For any components using
OnPush
change detection, ensure they are properly marked dirty to enable host binding updates.
Medium
Be aware that newly created views or views marked for check and reattached during change detection are now guaranteed to be refreshed in that same change detection cycle.
Advanced
After aligning the semantics of
ComponentFixture.whenStable
and
ApplicationRef.isStable
, your tests may wait longer when using
whenStable
.
Advanced
You may experience tests failures if you have tests that rely on change detection execution order when using
ComponentFixture.autoDetect
because it now executes change detection for fixtures within
ApplicationRef.tick
. For example, this will cause test fixture to refresh before any dialogs that it creates whereas this may have been the other way around in the past.
Advanced
In the application's project directory, run
ng update @angular/core@19 @angular/cli@19
to update your application to Angular v19.
Basic
Run
ng update @angular/material@19
.
Basic
Angular directives, components and pipes are now standalone by default. Specify "standalone: false" for declarations that are currently declared in an NgModule. The Angular CLI will automatically update your code to reflect that.
Basic
Remove
this.
prefix when accessing template reference variables. For example, refactor
<div #foo></div>{{ this.foo }}
to
<div #foo></div>{{ foo }}
Medium
Replace usages of
BrowserModule.withServerTransition()
with injection of the
APP_ID
token to set the application
id
instead.
Basic
The
factories
property in
KeyValueDiffers
has been removed.
Advanced
In angular.json, replace the "name" option with "project" for the
@angular/localize
builder.
Medium
Rename
ExperimentalPendingTasks
to
PendingTasks
.
Advanced
Update tests that relied on the
Promise
timing of effects to use
await whenStable()
or call
.detectChanges()
to trigger effects. For effects triggered during change detection, ensure they don't depend on the application being fully rendered or consider using
afterRenderEffect()
. Tests using faked clocks may need to fast-forward/flush the clock.
Medium
Upgrade to TypeScript version 5.5 or later.
Basic
Update tests using
fakeAsync
that rely on specific timing of zone coalescing and scheduling when a change happens outside the Angular zone (hybrid mode scheduling) as these timers are now affected by
tick
and
flush
.
Advanced
When using
createComponent
API and not passing content for the first
ng-content
, provide
document.createTextNode('')
as a
projectableNode
to prevent rendering the default fallback content.
Medium
Update tests that rely on specific timing or ordering of change detection around custom elements, as the timing may have changed due to the switch to the hybrid scheduler.
Advanced
Migrate from using
Router.errorHandler
to
withNavigationErrorHandler
from
provideRouter
or
errorHandler
from
RouterModule.forRoot
.
Basic
Update tests to handle errors thrown during
ApplicationRef.tick
by either triggering change detection synchronously or rejecting outstanding
ComponentFixture.whenStable
promises.
Advanced
Update usages of
Resolve
interface to include
RedirectCommand
in its return type.
Medium
fakeAsync
will flush pending timers by default. For tests that require the previous behavior, explicitly pass
{flush: false}
in the options parameter.
Advanced
In the application's project directory, run
ng update @angular/core@20 @angular/cli@20
to update your application to Angular v20.
Basic
Run
ng update @angular/material@20
.
Basic
Rename the
afterRender
lifecycle hook to
afterEveryRender
Basic
Replace uses of
TestBed.flushEffects()
with
TestBed.tick()
, the closest equivalent to synchronously flush effects.
Medium
Rename
provideExperimentalCheckNoChangesForDebug
to
provideCheckNoChangesConfig
. Note its behavior now applies to all
checkNoChanges
runs. The
useNgZoneOnStable
option is no longer available.
Advanced
Refactor application and test code to avoid relying on
ng-reflect-*
attributes. If needed temporarily for migration, use
provideNgReflectAttributes()
from
@angular/core
in bootstrap providers to re-enable them in dev mode only.
Advanced
Adjust code that directly calls functions returning
RedirectFn
. These functions can now also return an
Observable
or
Promise
; ensure your logic correctly handles these asynchronous return types.
Advanced
Rename the
request
property passed in resources to
params
.
Basic
Rename the
request
and
loader
properties passed in RxResource to
params
and
stream
.
Medium
ResourceStatus
is no longer an enum. Use the corresponding constant string values instead.
Basic
Rename
provideExperimentalZonelessChangeDetection
to
provideZonelessChangeDetection
.
Advanced
If your templates use
{{ in }}
or
in
in expressions to refer to a component property named 'in', change it to
{{ this.in }}
or
this.in
as 'in' now refers to the JavaScript 'in' operator. If you're using
in
as a template reference, you'd have to rename the reference.
Advanced
The type for the commands arrays passed to Router methods (
createUrlTree
,
navigate
,
createUrlTreeFromSnapshot
) have been updated to use
readonly T[]
since the array is not mutated. Code which extracts these types (e.g. with
typeof
) may need to be adjusted if it expects mutable arrays.
Advanced
Review and update tests asserting on DOM elements involved in animations. Animations are now guaranteed to be flushed with change detection or
ApplicationRef.tick
, potentially altering previous test outcomes.
Advanced
In tests, uncaught errors in event listeners are now rethrown by default. Previously, these were only logged to the console by default. Catch them if intentional for the test case, or use
rethrowApplicationErrors: false
in
configureTestingModule
as a last resort.
Medium
The
any
type is removed from the Route guard arrays (canActivate, canDeactivate, etc); ensure guards are functions,
ProviderToken<T>
, or (deprecated) strings. Refactor string guards to
ProviderToken<T>
or functions.
Advanced
Ensure your Node.js version is at least 20.11.1 and not v18 or v22.0-v22.10 before upgrading to Angular v20. Check
https://angular.dev/reference/versions
for the full list of supported Node.js versions.
Basic
Replace all occurrences of the deprecated
TestBed.get()
method with
TestBed.inject()
in your Angular tests for dependency injection.
Basic
Remove
InjectFlags
enum and its usage from
inject
,
Injector.get
,
EnvironmentInjector.get
, and
TestBed.inject
calls. Use options like
{optional: true}
for
inject
or handle null for
*.get
methods.
Medium
Update
injector.get()
calls to use a specific
ProviderToken<T>
instead of relying on the removed
any
overload. If using string tokens (deprecated since v4), migrate them to
ProviderToken<T>
.
Advanced
Upgrade your project's TypeScript version to at least 5.8 before upgrading to Angular v20 to ensure compatibility.
Basic
Unhandled errors in subscriptions/promises of AsyncPipe
are now directly reported to
ErrorHandler
. This may alter test outcomes; ensure tests correctly handle these reported errors.
Advanced
If relying on the return value of
PendingTasks.run
, refactor to use
PendingTasks.add
. Handle promise results/rejections manually, especially for SSR to prevent node process shutdown on unhandled rejections.
Advanced
If your templates use
{{ void }}
or
void
in expressions to refer to a component property named 'void', change it to
{{ this.void }}
or
this.void
as 'void' now refers to the JavaScript
void
operator.
Advanced
Review
DatePipe
usages. Using the
Y
(week-numbering year) formatter without also including
w
(week number) is now detected as suspicious. Use
y
(year) if that was the intent, or include
w
alongside
Y
.
Advanced
In templates parentheses are now always respected. This can lead to runtime breakages when nullish coalescing were nested in parathesis. eg
(foo?.bar).baz
will throw if
foo
is nullish as it would in native JavaScript.
Medium
Route configurations are now validated more rigorously. Routes that combine
redirectTo
and
canMatch
protections will generate an error, as these properties are incompatible together by default.
Advanced
In the application's project directory, run
ng update @angular/core@21 @angular/cli@21
to update your application to Angular v21.
Basic
Run
ng update @angular/material@21
.
Basic
When using signal inputs with Angular custom elements, update property access to be direct (
elementRef.newInput
) instead of a function call (
elementRef.newInput()
) to align with the behavior of decorator-based inputs.
Advanced
If using
provideZoneChangeDetection
without the ZoneJS polyfill, note that the internal scheduler is now always enabled. Review your app's timing as this may alter behavior that previously relied on the disabled scheduler.
Advanced
Zone-based applications should add
provideZoneChangeDetection()
to your application's root providers. For standalone apps, add it to the
bootstrapApplication
call. For NgModule-based apps, add it to your root
AppModule
's
providers
array. An automated migration should handle this.
Basic
Remove the 'interpolation' property from your @Component decorators. Angular now only supports the default '{{' and '}}' interpolation markers.
Advanced
Remove the 'moduleId' property from your @Component decorators. This property was used for resolving relative URLs for templates and styles, a functionality now handled by modern build tools.
Medium
The
ngComponentOutletContent
input has been strictly typed from
any[][]
to
Node[][]
. Update the value you pass to this input to match the new
Node[][] | undefined
type.
Medium
Host binding type checking is now enabled by default and may surface new build errors. Resolve any new type errors or set
typeCheckHostBindings: false
in your
tsconfig.json
's
angularCompilerOptions
.
Basic
Update your project's TypeScript version to 5.9 or later. The
ng update
command will typically handle this automatically.
Basic
The
ApplicationConfig
export from
@angular/platform-browser
has been removed. Update your imports to use
ApplicationConfig
from
@angular/core
instead.
Medium
The
ignoreChangesOutsideZone
option for configuring ZoneJS is no longer available. Remove this option from your ZoneJS configuration in your polyfills file.
Advanced
Update tests using
provideZoneChangeDetection
as TestBed now rethrows errors. Fix the underlying issues in your tests or, as a last resort, configure TestBed with
rethrowApplicationErrors: false
to disable this behavior.
Medium
Update tests that rely on router navigation timing. Navigations may now take additional microtasks to complete. Ensure navigations are fully completed before making assertions, for example by using
fakeAsync
with
flush
or waiting for promises/observables to resolve.
Medium
Tests using
TestBed
might be affected by the new fake
PlatformLocation
. If your tests fail, provide the old
MockPlatformLocation
from
@angular/common/testing
via
{provide: PlatformLocation, useClass: MockPlatformLocation}
in your
TestBed
configuration.
Medium
The
UpgradeAdapter
has been removed. Update your hybrid Angular/AngularJS application to use the static APIs from the
@angular/upgrade/static
package instead.
Advanced
The new standalone
formArray
directive might conflict with existing custom directives or inputs. Rename any custom directives named
FormArray
or inputs named
formArray
on elements that also use reactive forms to resolve the conflict.
Medium
The deprecated
NgModuleFactory
has been removed. Update any code that uses
NgModuleFactory
to use
NgModule
directly, which is common in dynamic component loading scenarios.
Advanced
The
emitDeclarationOnly
TypeScript compiler option is not supported. Please disable it in your
tsconfig.json
file to allow the Angular compiler to function correctly.
Advanced
The
lastSuccessfulNavigation
property on the Router has been converted to a signal. To get its value, you now need to invoke it as a function:
router.lastSuccessfulNavigation()
.
Medium
After you update
You don't need to do anything after moving between these versions.

