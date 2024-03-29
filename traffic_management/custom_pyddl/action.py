import pyddl


class Action(pyddl.Action):
    """Custom version of pyddl.Action to make use of the custom grounding method."""

    def __init__(self, *args, external_actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.external_actor = external_actor

    def ground(self, *args):
        return GroundedAction(self, *args)


class GroundedAction(object):
    """Customised pyddl._GroundAction, written to delay evaluation of the numerical effects to action application.

    Note: the original class was not suitable for subclassing due to two facts: being protected (underscore-starting
    name) and having most of the code to be changed put in a single method - __init__."""

    def __init__(self, action, *args):
        """Note: this method comes mostly from pyddl._GroundedAction.__init__; it has been split into sub-methods."""

        self.name = action.name
        self.external_actor = action.external_actor

        ground = self._grounder(action.arg_names, args)

        # Ground Action Signature
        self.sig = ground((self.name,) + action.arg_names)

        # Ground Preconditions
        self.preconditions = list()
        self.num_preconditions = list()
        self.ground_predicates(action, ground)

        # Ground Effects
        self.add_effects = list()
        self.del_effects = list()
        self.num_effects = list()
        self.ground_effects(action, ground, *args)

    def ground_effects(self, action, ground, *args):
        """Note: this method comes mostly from pyddl._GroundedAction.__init__.
        It is rewritten to change numerical effect values to functions, depending on action's arguments."""

        for effect in action.effects:
            if effect[0] == -1:
                self.del_effects.append(ground(effect[1]))
            elif effect[0] in ['+=', '-=']:
                function = ground(effect[1])
                value_sign = -1 if effect[0] == '-=' else 1
                value = (value_sign, effect[2], args)
                self.num_effects.append((function, value))
            else:
                self.add_effects.append(ground(effect))

    def ground_predicates(self, action, ground):
        """Note: this method comes from pyddl._GroundedAction.__init__"""

        for pre in action.preconditions:
            if pre[0] in pyddl.NUM_OPS:
                operands = [0, 0]
                for i in range(2):
                    if type(pre[i + 1]) == int:
                        operands[i] = pre[i + 1]
                    else:
                        operands[i] = ground(pre[i + 1])
                np = pyddl._num_pred(pyddl.NUM_OPS[pre[0]], *operands)
                self.num_preconditions.append(np)
            else:
                self.preconditions.append(ground(pre))

    @staticmethod
    def _grounder(arg_names, args):
        """
        Returns a function for grounding predicates and function symbols

        Note: this method comes entirely from the pyddl module
        """
        namemap = dict()
        for arg_name, arg in zip(arg_names, args):
            namemap[arg_name] = arg

        def _ground_by_names(predicate):
            return predicate[0:1] + tuple(namemap.get(arg, arg) for arg in predicate[1:])

        return _ground_by_names

    def evaluate_external(self):
        """Evaluate the effect of an action (one of possible actions) by consulting the external model."""

        return self.external_actor.evaluate_action[self.name](*self.sig[1:])

    def apply_external(self):
        """Apply the effects of the chosen action in the external model (i.e. update the model state)."""

        return self.external_actor.apply_action[self.name](*self.sig[1:])

    def __str__(self):
        """Note: this method is a copy of pyddl._GroundedAction"""

        arglist = ', '.join(map(str, self.sig[1:]))
        return '%s(%s)' % (self.sig[0], arglist)

