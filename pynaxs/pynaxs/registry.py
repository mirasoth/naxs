"""Catalog of standard operator types and parameter names.

``OPERATOR_REGISTRY`` lists the operator type names the validator
recognizes as standard, and ``STANDARD_PARAMS`` maps each type to the
parameter names commonly used with it. Both catalogs are advisory:
components with unknown types or non-standard parameter names remain
valid and only trigger soft validation warnings, never errors.
"""

# Standard operator type names, grouped by category.
OPERATOR_REGISTRY = {
    # Core / IO
    "input", "output", "custom",
    # Structural
    "add", "concatenate", "transformerBlock",
    # Normalization
    "layerNorm", "rmsNorm", "batchNorm", "groupNorm",
    # Attention
    "multiHeadAttention", "groupedQueryAttention", "attention", "mla",
    "slidingWindowAttention", "sparseAttention",
    # Feed-Forward
    "feedForward", "swiglu", "geglu",
    # Linear
    "linear", "embedding",
    # Convolution
    "conv2d", "depthwiseConv2d", "conv1d", "conv3d",
    # Activation
    "relu", "gelu", "silu", "sigmoid", "tanh",
    # Pooling
    "maxPool2d", "avgPool2d", "adaptiveAvgPool2d", "globalAvgPool",
    # Specialized
    "moeLayer", "sharedExpertMoE", "seBlock", "patchEmbed",
    "positionalEncoding", "dropout", "flatten", "reshape",
    # Recurrent
    "lstm", "gru",
    # SSM
    "selectiveSsm", "mambaBlock",
    # Detection
    "featurePyramidNetwork", "roiAlign",
    # Loss
    "crossEntropyLoss", "focalLoss",
    # Misc
    "stochasticDepth", "emaWeights",
}

# Standard parameter names per operator type, used for soft validation
# warnings. An empty set means the type takes no standard parameters;
# a None value (currently only "custom") means any parameter names are
# accepted without warning.
STANDARD_PARAMS: dict[str, set[str]] = {
    "input": {"shape"},
    "output": {"shape"},
    "linear": {"inFeatures", "outFeatures", "bias"},
    "embedding": {"vocabSize", "embeddingDim", "maxSeqLen", "numEmbeddings"},
    "conv2d": {"inChannels", "outChannels", "kernelSize", "stride", "padding", "bias", "dilation", "groups"},
    "depthwiseConv2d": {"inChannels", "outChannels", "kernelSize", "stride", "padding"},
    "conv1d": {"inChannels", "outChannels", "kernelSize", "stride", "padding"},
    "multiHeadAttention": {"numHeads", "hiddenDim", "embedDim"},
    "groupedQueryAttention": {"numHeads", "embedDim", "numKVHeads", "headDim"},
    "attention": {"hiddenDim", "numHeads"},
    "mla": {"embedDim", "numHeads", "kvLatentDim", "qLatentDim", "ropeHeadDim"},
    "layerNorm": {"normalizedShape", "eps"},
    "rmsNorm": {"normalizedShape", "eps"},
    "batchNorm": {"numFeatures", "eps", "momentum"},
    "feedForward": {"embedDim", "hiddenDim", "ffDim"},
    "swiglu": {"embedDim", "hiddenDim", "dim", "intermediateSize"},
    "geglu": {"embedDim", "hiddenDim", "dim", "intermediateSize"},
    "moeLayer": {"embedDim", "numExperts", "expertDim", "topK"},
    "sharedExpertMoE": {"embedDim", "numExperts", "expertDim", "topK", "numSharedExperts"},
    "seBlock": {"channels", "reduction"},
    "patchEmbed": {"imgSize", "patchSize", "embedDim", "inChans"},
    "add": set(),
    "concatenate": {"dim", "axis", "numInputs"},
    "transformerBlock": {"embedDim", "numHeads", "hiddenDim", "ffDim"},
    "positionalEncoding": {"embedDim", "maxSeqLen", "embeddingDim"},
    "dropout": {"p"},
    "relu": set(),
    "gelu": set(),
    "silu": set(),
    "sigmoid": set(),
    "tanh": set(),
    "maxPool2d": {"kernelSize", "stride", "padding"},
    "avgPool2d": {"kernelSize", "stride", "padding"},
    "adaptiveAvgPool2d": {"outputSize"},
    "globalAvgPool": set(),
    "flatten": set(),
    "reshape": {"shape"},
    "lstm": {"inputSize", "hiddenSize", "numLayers"},
    "gru": {"inputSize", "hiddenSize", "numLayers"},
    "selectiveSsm": {"dModel", "dState", "dConv"},
    "mambaBlock": {"dModel", "dState", "dConv", "expand"},
    "stochasticDepth": {"p"},
    "emaWeights": {"decay"},
    "crossEntropyLoss": set(),
    "focalLoss": {"alpha", "gamma"},
    "custom": None,  # None means: any params are fine, don't warn
}
