# Angular Migration Guide: v13

Platform server and lazy loading updates.

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
