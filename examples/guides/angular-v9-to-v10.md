# Angular Migration Guide: v9 to v10

Ivy compiler introduction and initial stabilization.

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
