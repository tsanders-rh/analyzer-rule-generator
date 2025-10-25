import React from 'react';
import { Chip, Tile, Text, ExpandableSection, EmptyState } from '@patternfly/react-core';
import { Chart } from '@patternfly/react-charts';

// This file contains PatternFly v5 patterns that should trigger migration rules

const App: React.FC = () => {
  return (
    <div>
      {/* Rule: Chip should be replaced with Label */}
      <Chip>Deprecated Chip Component</Chip>

      {/* Rule: Tile should be replaced with Card */}
      <Tile title="Deprecated Tile">
        Content here
      </Tile>

      {/* Rule: Text should be replaced with Content */}
      <Text component="p">
        This uses the deprecated Text component
      </Text>

      {/* Rule: ExpandableSection isActive prop removal */}
      <ExpandableSection isActive={true}>
        This prop is deprecated
      </ExpandableSection>

      {/* Rule: EmptyState refactoring */}
      <EmptyState>
        <p>This component structure has changed</p>
      </EmptyState>

      {/* Rule: Chart import path change */}
      <Chart
        ariaTitle="Example Chart"
        height={200}
        width={400}
      />
    </div>
  );
};

export default App;
