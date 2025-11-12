import React from 'react';
import { Text } from '@patternfly/react-core';
import { Chip } from '@patternfly/react-core';
import { Button, Card, CardBody, ExpandableSection } from '@patternfly/react-core';
import { Chart, ChartAxis } from '@patternfly/react-charts';
import './styles.css';

// This component uses PatternFly v5 patterns that need migration to v6
const App: React.FC = () => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  return (
    <div className="app-container">
      <Card>
        <CardBody>
          {/* Text component should be renamed to Content in v6 */}
          <Text component="h1">PatternFly v5 Test Application</Text>

          {/* Chip component should be replaced with Label in v6 */}
          <Chip>Tag 1</Chip>
          <Chip>Tag 2</Chip>

          {/* ExpandableSection with isActive prop (removed in v6) */}
          <ExpandableSection
            isActive={isExpanded}
            toggleText="Show more"
            onToggle={() => setIsExpanded(!isExpanded)}
          >
            <p>This is expandable content</p>
          </ExpandableSection>

          <Button variant="primary">Click me</Button>

          {/* Chart imports from @patternfly/react-charts */}
          <Chart height={200} width={400}>
            <ChartAxis />
          </Chart>
        </CardBody>
      </Card>
    </div>
  );
};

export default App;
