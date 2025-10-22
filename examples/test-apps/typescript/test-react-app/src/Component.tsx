import React from 'react';
import PropTypes from 'prop-types';
import { Route } from 'react-router';

// This should trigger typescript-provider-test-00000 (propTypes on function component)
function MyComponent(props: any) {
  return <div>{props.name}</div>;
}

MyComponent.propTypes = {
  name: PropTypes.string
};

// This should trigger typescript-provider-test-00010 (React.FC usage)
const AnotherComponent: React.FC<{ title: string }> = ({ title }) => {
  return <h1>{title}</h1>;
};

// This should trigger typescript-provider-test-00030 (deprecated lifecycle method)
class LegacyComponent extends React.Component {
  componentWillMount() {
    console.log('Component will mount');
  }

  render() {
    return <div>Legacy Component</div>;
  }
}

// This file imports from react-router, should trigger typescript-provider-test-00040
export { MyComponent, AnotherComponent, LegacyComponent };
