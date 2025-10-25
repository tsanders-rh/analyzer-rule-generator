// PatternFly v5 React token patterns that should trigger migration rules

import {
  global_FontSize_lg,
  global_Color_100,
  global_spacer_md
} from '@patternfly/react-tokens';

// Rule: React token syntax change
// These should change from global_* to t_global_*
export const styles = {
  fontSize: global_FontSize_lg.value,
  color: global_Color_100.value,
  padding: global_spacer_md.value,
};
