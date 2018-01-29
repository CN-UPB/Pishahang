#encoding: utf-8
lib = File.expand_path("../lib", __FILE__)
$LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
require "SONATA/version"

Gem::Specification.new do |spec|
  spec.name          = "SONATA"
  spec.version       = SONATA::VERSION
  spec.authors       = ["José Bonnet"]
  spec.email         = ["jose.bonnet@gmail.com"]

  spec.summary       = %q{A small library to make working with [curb](https://github.com/taf2/curb) easier}
  spec.description   = %q{[Curb](https://github.com/taf2/curb) is a great ruby gem, but working with it demands repeating some code. Therefore this gem.}
  spec.homepage      = "https://github.com/sonata-nfv/son-gkeeper"
  spec.license       = "Apache2"

  # Prevent pushing this gem to RubyGems.org. To allow pushes either set the 'allowed_push_host'
  # to allow pushing to a single host or delete this section to allow pushing to any host.
  #if spec.respond_to?(:metadata)
  #  spec.metadata["allowed_push_host"] = "Set to 'http://mygemserver.com'"
  #else
  #  raise "RubyGems 2.0 or newer is required to protect against public gem pushes."
  #end

  spec.files         = ["lib/SONATA.rb"]
  #`git ls-files -z`.split("\x0").reject do |f|
  #  f.match(%r{^(test|spec|features)/})
  #end
  spec.bindir        = "exe"
  spec.executables   = spec.files.grep(%r{^exe/}) { |f| File.basename(f) }
  spec.require_paths = ["lib"]

  spec.add_development_dependency "bundler", "~> 1.16"
  spec.add_development_dependency "rake", "~> 10.0"
  spec.add_development_dependency "rspec", "~> 3.0"
  spec.add_runtime_dependency "curb", "~> 0.9.3"
end
