# React 18 Upgrade Guide - Demo Version

This is a condensed version of the React 18 migration guide for quick demos.

## New Root API

React 18 introduces a new root API which provides better ergonomics for managing roots.

### ReactDOM.render is deprecated

In React 17:
```jsx
import ReactDOM from 'react-dom';
ReactDOM.render(<App />, document.getElementById('root'));
```

In React 18:
```jsx
import ReactDOM from 'react-dom/client';
const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
```

## Automatic Batching

React 18 adds out-of-the-box performance improvements by doing more batching by default.

### What changed

Before React 18, we only batched updates inside React event handlers. Updates inside promises, setTimeout, native event handlers, or any other event were not batched by default.

In React 18, all updates will be automatically batched, no matter where they originate from.

If you need to opt out of automatic batching, you can use `flushSync`:

```jsx
import { flushSync } from 'react-dom';

flushSync(() => {
  setCounter(c => c + 1);
});
```

## Suspense Improvements

### Suspense on the Server

React 18 includes architectural improvements to React server-side rendering (SSR) performance. The new SSR architecture supports `Suspense` on the server.

You can now use `<Suspense>` to break down your app into smaller independent units:

```jsx
<Suspense fallback={<Spinner />}>
  <Comments />
</Suspense>
```

### Suspense for Data Fetching

In React 18, you can use Suspense to declaratively specify the loading state for a part of the component tree if it's not yet ready to be displayed:

```jsx
<Suspense fallback={<Spinner />}>
  <ProfilePage />
</Suspense>
```

## Concurrent Features

### startTransition

`startTransition` lets you mark certain updates as "transitions" which tells React they can be interrupted:

Before (React 17):
```jsx
setInputValue(input);
setSearchQuery(input);
```

After (React 18):
```jsx
import { startTransition } from 'react';

setInputValue(input);
startTransition(() => {
  setSearchQuery(input);
});
```

### useDeferredValue

`useDeferredValue` lets you defer re-rendering a non-urgent part of the tree:

```jsx
import { useDeferredValue } from 'react';

function SearchResults() {
  const deferredQuery = useDeferredValue(query);
  // ...
}
```

## Strict Mode Changes

In React 18, Strict Mode will simulate mounting, unmounting, and re-mounting the component with previous state.

This is a development-only behavior and does not affect production.

## Removed: Partial Hydration Warnings

React 18 removes some warnings that were previously shown during hydration mismatches, as the new streaming SSR architecture handles these cases better.

## New Hooks

### useId

`useId` is a new hook for generating unique IDs on both the client and server:

```jsx
import { useId } from 'react';

function PasswordField() {
  const passwordHintId = useId();
  return (
    <>
      <input type="password" aria-describedby={passwordHintId} />
      <p id={passwordHintId}>
        Password should contain at least 8 characters
      </p>
    </>
  );
}
```

### useSyncExternalStore

`useSyncExternalStore` is a new hook that allows external stores to support concurrent reads:

```jsx
import { useSyncExternalStore } from 'react';

const state = useSyncExternalStore(
  store.subscribe,
  store.getSnapshot
);
```

### useInsertionEffect

`useInsertionEffect` is a new hook for CSS-in-JS libraries:

```jsx
import { useInsertionEffect } from 'react';

useInsertionEffect(() => {
  // Inject styles
}, []);
```

## TypeScript Changes

The types for `ReactDOM.render` have been updated. You may see new TypeScript errors if you're upgrading from React 17.

The new `createRoot` API is fully typed:

```typescript
import { createRoot } from 'react-dom/client';

const container = document.getElementById('root')!;
const root = createRoot(container);
root.render(<App />);
```
