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
