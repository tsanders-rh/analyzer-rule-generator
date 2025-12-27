# Angular Migration Guide: v15

Standalone components preparation and Material MDC migration.

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
