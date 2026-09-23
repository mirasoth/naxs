"""Standard operator type registry and parameter name catalog.

Derived from NAXS spec Appendix A & B — based on statistical analysis
of 288 architectures (9,735 components, 79 distinct operator types).
These are *recommended* names, not required — non-matching names produce
soft validation warnings, not errors.
"""

# Standard operator types (79 observed in the Atlas knowledge base)
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

# Standard parameter names per operator type (for soft validation warnings).
# Maps operator type -> set of known parameter names.
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
    "mla": {"kvLatentDim", "qLatentDim", "ropeHeadDim"},
    "layerNorm": {"normalizedShape", "eps"},
    "rmsNorm": {"normalizedShape", "eps"},
    "batchNorm": {"numFeatures", "eps", "momentum"},
    "feedForward": {"hiddenDim", "ffDim"},
    "swiglu": {"dim", "intermediateSize"},
    "geglu": {"dim", "intermediateSize"},
    "moeLayer": {"numExperts", "expertDim", "topK"},
    "sharedExpertMoE": {"numExperts", "expertDim", "topK", "numSharedExperts"},
    "seBlock": {"channels", "reduction"},
    "patchEmbed": {"imgSize", "patchSize", "embedDim", "inChans"},
    "add": set(),
    "concatenate": set(),
    "transformerBlock": {"numHeads", "hiddenDim", "ffDim"},
    "positionalEncoding": {"maxSeqLen", "embeddingDim"},
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
